// ローカル確認用ダミーデータ（Q-P4=A）。VITE_API_BASE_URL 未設定時に使用。
import type { EventDetail, Notice, Post } from "./types";

export const dummyPosts: Post[] = [
  {
    post_id: "d1",
    title: "春の体験練習会を開催しました",
    author_display_name: "コーチ 田中",
    category: "活動報告",
    published_at: "2026-04-14T10:00:00+09:00",
    body:
      "先週末、春の体験練習会を開催しました。たくさんのお友だちが参加してくれて、" +
      "元気いっぱいドリブルやシュートに挑戦していました。\n\n次回は5月を予定しています。お気軽にご参加ください！",
  },
  {
    post_id: "d2",
    title: "ミニバス交流大会に参加しました",
    author_display_name: "IYフレンズ",
    category: "イベント",
    published_at: "2026-03-20T09:00:00+09:00",
    body: "近隣チームとの交流大会に参加しました。最後まであきらめずに走り切りました！",
  },
  {
    post_id: "d3",
    title: "新しいユニフォームが届きました",
    author_display_name: "コーチ 佐藤",
    category: "お知らせ",
    published_at: "2026-02-28T09:00:00+09:00",
    body: "今シーズンから新デザインのユニフォームになります。チームカラーが目印です。",
  },
];

export const dummyNotices: Notice[] = [
  {
    notice_id: "n1",
    title: "5月の練習スケジュールについて",
    published_at: "2026-04-25T09:00:00+09:00",
    body: "5月の練習は毎週土曜 9:00〜11:00、市民体育館にて行います。",
  },
  {
    notice_id: "n2",
    title: "会費納入のお願い",
    published_at: "2026-04-10T09:00:00+09:00",
    body: "今年度の会費納入をお願いいたします。詳細は配布のプリントをご確認ください。",
  },
];

export const dummyEvents: EventDetail[] = [
  {
    event_id: "e1",
    title: "練習試合（vs さくらミニバス）",
    location: "市民体育館 メインアリーナ",
    event_date: "2026-05-10T10:00:00+09:00",
    description: "近隣チームとの練習試合です。応援よろしくお願いします。",
  },
  {
    event_id: "e2",
    title: "体験練習会",
    location: "市民体育館 サブアリーナ",
    event_date: "2026-05-17T09:30:00+09:00",
    description: "未就学〜小学生対象の体験会。持ち物は室内用シューズ・運動できる服装と飲み物。",
  },
];
