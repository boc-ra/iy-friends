import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { RequireAuth, RequireRole } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Loading } from "./components/ui";

const CalendarAdmin = lazy(() => import("./pages/CalendarAdmin").then((module) => ({ default: module.CalendarAdmin })));
const Dashboard = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.Dashboard })));
const EventEdit = lazy(() => import("./pages/EventEdit").then((module) => ({ default: module.EventEdit })));
const InquiryDetail = lazy(() => import("./pages/InquiryDetail").then((module) => ({ default: module.InquiryDetail })));
const InquiryList = lazy(() => import("./pages/InquiryList").then((module) => ({ default: module.InquiryList })));
const Login = lazy(() => import("./pages/Login").then((module) => ({ default: module.Login })));
const NoticeEdit = lazy(() => import("./pages/NoticeEdit").then((module) => ({ default: module.NoticeEdit })));
const NoticeList = lazy(() => import("./pages/NoticeList").then((module) => ({ default: module.NoticeList })));
const NotFound = lazy(() => import("./pages/NotFound").then((module) => ({ default: module.NotFound })));
const PostEdit = lazy(() => import("./pages/PostEdit").then((module) => ({ default: module.PostEdit })));
const PostList = lazy(() => import("./pages/PostList").then((module) => ({ default: module.PostList })));
const Profile = lazy(() => import("./pages/Profile").then((module) => ({ default: module.Profile })));
const UserList = lazy(() => import("./pages/UserList").then((module) => ({ default: module.UserList })));

export default function App() {
  return (
    <Suspense fallback={<Loading label="画面を読み込み中…" />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth><Layout /></RequireAuth>}>
          <Route index element={<Dashboard />} />
          <Route path="/posts" element={<PostList />} />
          <Route path="/posts/new" element={<PostEdit />} />
          <Route path="/posts/:id" element={<PostEdit />} />
          <Route path="/notices" element={<NoticeList />} />
          <Route path="/notices/new" element={<NoticeEdit />} />
          <Route path="/notices/:id" element={<NoticeEdit />} />
          <Route path="/calendar" element={<CalendarAdmin />} />
          <Route path="/calendar/new" element={<EventEdit />} />
          <Route path="/calendar/:id" element={<EventEdit />} />
          <Route path="/inquiries" element={<RequireRole roles={["admin"]}><InquiryList /></RequireRole>} />
          <Route path="/inquiries/:id" element={<RequireRole roles={["admin"]}><InquiryDetail /></RequireRole>} />
          <Route path="/users" element={<RequireRole roles={["admin"]}><UserList /></RequireRole>} />
          <Route path="/profile" element={<Profile />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
