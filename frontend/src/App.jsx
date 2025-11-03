import { useState, useEffect } from "react";
import axios from "axios";

export default function App() {
  const [temp, setTemp] = useState(null);
  const [isOn, setIsOn] = useState(false); // camelCase fixed

  // 🔹 Fetch temperature data every 5 seconds
  useEffect(() => {
    const fetchData = () => {
      axios
        .get("/temp")
        .then((res) => setTemp(res.data))
        .catch((err) => console.log("Error getting temp", err));
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // 🔹 Fetch light status every 5 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/light/status");
        const data = await res.json();
        setIsOn(data.on); // ✅ use the 'on' field from JSON
      } catch (err) {
        console.error("Failed to fetch light status:", err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // 🔹 Toggle handler for light on/off
  const toggleLight = async () => {
    try {
      await fetch("/light/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ desired: !isOn }),
      });
      setIsOn(!isOn);
    } catch (err) {
      console.error("Failed to toggle light:", err);
    }
  };

  // 🧠 Circle fill logic (for a little animation)
  const dashOffset =
    temp && temp.temperature
      ? 282 - ((temp.temperature - 70) / 10) * 20 // simple ratio scaling
      : 282;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-100 to-orange-50 text-gray-800 font-sans">
      {/* Header */}
      <header className="absolute top-6 flex flex-col items-center">
        <h1 className="text-xl font-semibold">Aquarium R4</h1>
        <div className="text-sm text-blue-600 flex items-center gap-1">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          Connected
        </div>
      </header>

      {/* Temperature Display */}
      <div className="relative mt-10 w-56 h-56 flex items-center justify-center">
        <svg className="absolute inset-0 transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="#e5e7eb"
            strokeWidth="6"
            fill="none"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="#5187deff"
            strokeWidth="6"
            fill="none"
            strokeDasharray="282"
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
          />
        </svg>
        <div className="text-center">
          <p className="text-sm text-gray-500">Temperature</p>
          <h2 className="text-3xl font-bold">
            {temp ? `${temp.temperature}°F` : "--"}
          </h2>
          <p className="text-xs text-gray-400 mt-1">Ideal: 78°F</p>
        </div>
      </div>

      {/* Info */}
      <div className="mt-8 text-center">
        <p className="text-lg font-medium">
          Mode:{" "}
          <span className="text-blue-600">
            {isOn ? "Daylight" : "Night"}
          </span>
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Last Fed: {temp ? temp.lastFed || "--" : "--"}
        </p>
      </div>

      {/* Toggle Button */}
      <button
        onClick={toggleLight}
        className={`mt-4 px-4 py-2 rounded-lg font-semibold text-white ${
          isOn ? "bg-blue-600" : "bg-gray-400"
        }`}
      >
        {isOn ? "Light ON" : "Light OFF"}
      </button>
    </div>
  );
}
