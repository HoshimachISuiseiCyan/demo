import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";

export default function App() {
  return (
    <div className="flex">
      <Sidebar />
      <Home />
    </div>
  );
}