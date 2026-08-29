"""DynamoDB アクセス基盤（SECURITY-05 / SECURITY-06）。

- パラメータ化された Query/GetItem/PutItem のみ。Scan は使わない。
- boto3 標準の指数バックオフ・限定リトライを設定（無限リトライ禁止, NFR-U3-REL）。
- リポジトリはこの基底を継承し、テーブル単位で最小権限アクセスを行う。
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

from src.common.config import AWS_REGION


def _plain_key(key: dict | None) -> dict | None:
    """LastEvaluatedKey（次ページカーソル）内の Decimal を int へ正規化する。

    DynamoDB は数値を Decimal で返すため、そのまま json.dumps するとエラーになる。
    カーソルのキーは文字列か整数（epoch/ID）なので int へ変換して JSON 化可能にする。
    """
    if not key:
        return None
    return {k: (int(v) if isinstance(v, Decimal) else v) for k, v in key.items()}

# 限定リトライ（最大3回, 指数バックオフ）。
_BOTO_CONFIG = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "standard"},
)


@lru_cache(maxsize=1)
def _resource():
    return boto3.resource("dynamodb", config=_BOTO_CONFIG)


class Repository:
    """テーブル単位アクセスの基底クラス。"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._table = _resource().Table(table_name)

    def get(self, key: dict) -> dict | None:
        """主キー指定で1件取得（GetItem）。"""
        resp = self._table.get_item(Key=key)
        return resp.get("Item")

    def put(self, item: dict, condition=None) -> None:
        """1件保存（PutItem）。condition で冪等・上書き防止に利用可。"""
        kwargs: dict = {"Item": item}
        if condition is not None:
            kwargs["ConditionExpression"] = condition
        self._table.put_item(**kwargs)

    def update_item(self, key: dict, updates: dict, condition=None) -> None:
        """指定属性を SET 更新（UpdateItem）。updates は {属性名: 値}。

        属性名は予約語衝突回避のため ExpressionAttributeNames で別名化する。
        condition で存在確認・楽観制御に利用可。
        """
        if not updates:
            return
        set_parts = []
        names: dict = {}
        values: dict = {}
        for i, (attr, value) in enumerate(updates.items()):
            names[f"#a{i}"] = attr
            values[f":v{i}"] = value
            set_parts.append(f"#a{i} = :v{i}")
        kwargs: dict = {
            "Key": key,
            "UpdateExpression": "SET " + ", ".join(set_parts),
            "ExpressionAttributeNames": names,
            "ExpressionAttributeValues": values,
        }
        if condition is not None:
            kwargs["ConditionExpression"] = condition
        self._table.update_item(**kwargs)

    def delete(self, key: dict, condition=None) -> None:
        """1件削除（DeleteItem）。condition で存在確認に利用可。"""
        kwargs: dict = {"Key": key}
        if condition is not None:
            kwargs["ConditionExpression"] = condition
        self._table.delete_item(**kwargs)

    def scan_all(self, *, limit: int | None = None) -> list[dict]:
        """全件取得（Scan）。**小規模テーブル（例: Users ≤10）専用**の限定用途。

        大規模テーブルでは使わない（コスト/性能。原則は query_index）。
        """
        kwargs: dict = {}
        if limit is not None:
            kwargs["Limit"] = limit
        items: list[dict] = []
        resp = self._table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        # 小規模前提のため1ページで十分だが、念のため継続キーを追う。
        while "LastEvaluatedKey" in resp and (limit is None or len(items) < limit):
            resp = self._table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
            items.extend(resp.get("Items", []))
        return items[:limit] if limit is not None else items

    def query_index(
        self,
        index_name: str,
        key_name: str,
        key_value,
        *,
        limit: int,
        ascending: bool = False,
        start_key: dict | None = None,
    ) -> tuple[list[dict], dict | None]:
        """GSI をパーティションキー等価で Query（Scan 回避）。

        戻り値: (items, next_start_key)。next が None ならページ終端。
        """
        kwargs: dict = {
            "IndexName": index_name,
            "KeyConditionExpression": Key(key_name).eq(key_value),
            "Limit": limit,
            "ScanIndexForward": ascending,
        }
        if start_key:
            kwargs["ExclusiveStartKey"] = start_key
        resp = self._table.query(**kwargs)
        return resp.get("Items", []), _plain_key(resp.get("LastEvaluatedKey"))

    def query_recent_by(
        self,
        index_name: str,
        key_name: str,
        key_value,
        *,
        since_epoch: int,
        range_key: str,
    ) -> list[dict]:
        """指定 GSI で range_key >= since_epoch の項目を取得（軽量冪等チェック等）。"""
        kwargs = {
            "IndexName": index_name,
            "KeyConditionExpression": Key(key_name).eq(key_value)
            & Key(range_key).gte(since_epoch),
        }
        resp = self._table.query(**kwargs)
        return resp.get("Items", [])
