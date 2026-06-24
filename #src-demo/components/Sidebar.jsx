import { useStore } from "../store/useStore";

export default function Sidebar() {
  const {
    libraries,
    currentLibId,
    setCurrentLib,
    addLibrary,
    deleteLibrary,
    renameLibrary,
  } = useStore();

  return (
    <div className="w-64 bg-gray-900 text-white h-screen p-4">
      <h2 className="text-xl mb-4">📚 题库</h2>

      {libraries.map((lib) => (
        <div
          key={lib.id}
          className={`p-2 rounded cursor-pointer ${
            lib.id === currentLibId ? "bg-blue-500" : "bg-gray-700"
          }`}
          onClick={() => setCurrentLib(lib.id)}
        >
          <div className="flex justify-between">
            <span>{lib.name}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteLibrary(lib.id);
              }}
            >
              ❌
            </button>
          </div>
        </div>
      ))}

      <button
        className="mt-4 w-full bg-green-500 p-2 rounded"
        onClick={addLibrary}
      >
        + 新建题库
      </button>
    </div>
  );
}