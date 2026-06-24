import Sidebar from "../components/Sidebar";
import QuestionCard from "../components/QuestionCard";
import UploadPanel from "../components/UploadPanel";

export default function Home() {
  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col items-center justify-center bg-gray-100">
        <UploadPanel />
        <QuestionCard />
      </div>
    </div>
  );
}