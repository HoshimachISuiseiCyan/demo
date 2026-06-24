import { useStore } from "../store/useStore";

export default function Sidebar() {
  const { banks, switchBank, addBank } = useStore();

  return (
    <div className="w-64 bg-gray-900 text-white p-4 flex flex-col">
      <h2 className="text-xl mb-4">题库</h2>

      {banks.map(b => (
        <div
          key={b.id}
          onClick={() => switchBank(b.id)}
          className="p-2 rounded hover:bg-gray-700 cursor-pointer"
        >
          {b.name}
        </div>
      ))}

      <button
        onClick={addBank}
        className="mt-4 bg-blue-500 p-2 rounded"
      >
        ＋ 新建题库
      </button>
    </div>
  );
}