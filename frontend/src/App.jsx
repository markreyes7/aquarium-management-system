import { useState, useEffect } from "react";
import MiniNav from "./components/MiniNav"
import axios from "axios";

export default function App() {
  const [temp, setTemp] = useState(null);

  const [currentSection, setCurrentSection] = useState("temp");

  const handleNavChange = (section) => {
    console.log("Selected:", section);
    setCurrentSection(section);
  };

  useEffect(() => {
    axios.get("/temp")
      .then(res => setTemp(res.data))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
  axios.get("/temp").then(res => {
    console.log("Backend response:", res.data);
  });
}, []);

  

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-100 to-orange-50 text-gray-800 font-sans">
      
      <header className="absolute top-6 flex flex-col items-center">
        <h1 className="text-xl font-semibold">Aquarium R4</h1>
        <div className="text-sm text-blue-600 flex items-center gap-1">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          Connected
        </div>
      </header>

      
      <div className="relative mt-10 w-56 h-56 flex items-center justify-center">
        <svg className="absolute inset-0 transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="45"
            stroke="#e5e7eb" strokeWidth="6" fill="none"
          />
          <circle
            cx="50" cy="50" r="45"
            stroke="#5187deff" strokeWidth="6" fill="none"
            strokeDasharray="282"
            strokeDashoffset= ""
            strokeLinecap="round"
          />
        </svg>
        <div className="text-center">
          <p className="text-sm text-gray-500">Temperature</p>
          <h2 className="text-3xl font-bold">
            {temp ? `${temp.temperature}°F` : "--"}
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Ideal: 78°F
          </p>
        </div>
      </div>

      
      <div className="mt-8 text-center">
        <p className="text-lg font-medium">
          Mode: <span className="text-blue-600">{temp?.lightsOn ? "Daylight" : "Night"}</span>
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Last Fed: {temp ? temp.lastFed : "--"}
        </p>
      </div>

      
    </div>
  );
}
