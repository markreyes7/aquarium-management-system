// src/components/MiniNav.jsx
import { useState } from "react";
import { Thermometer, Droplets, Sun, Settings } from "lucide-react";
import NavItem from "./NavItem";

export default function MiniNav({ onSelect }) {
  const [active, setActive] = useState("temp");

  const handleSelect = (id) => {
    setActive(id);
    if (onSelect) onSelect(id);
  };

  const items = [
    { id: "temp", label: "Temperature", icon: Thermometer },
    { id: "hardness", label: "Hardness", icon: Droplets },
    { id: "light", label: "Light", icon: Sun },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <div className="flex justify-around items-center bg-gray-900 text-white rounded-2xl mt-4 shadow-md">
      {items.map((item) => (
        <NavItem
          key={item.id}
          icon={item.icon}
          label={item.label}
          active={active === item.id}
          onClick={() => handleSelect(item.id)}
        />
      ))}
    </div>
  );
}
