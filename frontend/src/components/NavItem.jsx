// src/components/NavItem.jsx
export default function NavItem({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center justify-center w-full py-3 transition-colors
        ${active ? "text-emerald-400" : "text-gray-400 hover:text-emerald-300"}
      `}
    >
      <Icon size={22} />
      <span className="text-xs mt-1">{label}</span>
    </button>
  );
}
