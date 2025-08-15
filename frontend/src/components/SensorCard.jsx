export default function SensorCard({ name, value, unit }) {
  return (
    <div className="rounded- border bg-white p-4 shadow-sm">
      <div className="text-sm text-gray-500">{name}</div>
      <div className="text-3xl font-semibold">
        {value}{unit ? ` ${unit}` : ''}
      </div>
    </div>
  )
}
