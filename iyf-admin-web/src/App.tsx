import { Route, Routes } from "react-router-dom";
import { RequireAuth, RequireRole } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { CalendarAdmin } from "./pages/CalendarAdmin";
import { Dashboard } from "./pages/Dashboard";
import { EventEdit } from "./pages/EventEdit";
import { InquiryDetail } from "./pages/InquiryDetail";
import { InquiryList } from "./pages/InquiryList";
import { Login } from "./pages/Login";
import { NoticeEdit } from "./pages/NoticeEdit";
import { NoticeList } from "./pages/NoticeList";
import { NotFound } from "./pages/NotFound";
import { PostEdit } from "./pages/PostEdit";
import { PostList } from "./pages/PostList";
import { Profile } from "./pages/Profile";
import { UserList } from "./pages/UserList";

export default function App() {
  return (
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
  );
}
