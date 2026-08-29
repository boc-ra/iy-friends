import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { About } from "./pages/About";
import { BlogDetail } from "./pages/BlogDetail";
import { BlogList } from "./pages/BlogList";
import { Calendar } from "./pages/Calendar";
import { Contact } from "./pages/Contact";
import { Home } from "./pages/Home";
import { Join } from "./pages/Join";
import { NotFound } from "./pages/NotFound";
import { Notices } from "./pages/Notices";
import { Terms } from "./pages/Terms";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="/blog" element={<BlogList />} />
        <Route path="/blog/:id" element={<BlogDetail />} />
        <Route path="/notices" element={<Notices />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/about" element={<About />} />
        <Route path="/join" element={<Join />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
