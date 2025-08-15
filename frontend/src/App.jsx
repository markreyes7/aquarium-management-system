import { use, useEffect, useState } from 'react'
import SensorCard from './components/SensorCard.jsx'

export default function App() {
  const [items, setItems] = useState([])
  const [datas, setData] = useState([])
  const [error, setError] = useState(null)

  // useEffect(() => {
  //   let alive = true
  //   fetch('/items')            
  //     .then(res => {
  //       if (!res.ok) throw new Error(`HTTP ${res.status}`)
  //       return res.json()
  //     })
  //     .then(json => { if (alive) setItems(json) })
  //     .catch(e => { if (alive) setError(e) }) //changes our stateful value
  //   return () => { alive = false }
  // }, [])

  useEffect(() => {
    let alive = true
    fetch('/getData')            
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(json => { if (alive) setData(json) })
      .catch(e => { if (alive) setError(e) }) //changes our stateful value
    return () => { alive = false }
  }, [])

  if (error) return <div className="p-6 text-red-600">Error: {error.message}</div> //this catches the errors during the first time rendering. 
  if (!items.length) return <div className="p-6">Loading…</div>

  return (
    <div className="min-h-screen bg-blue-50 p-6">
      <h1 className="text-3xl font-bold mb-6">Aquarium Dashboard</h1>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(it => (
          <SensorCard key={it.id} name={it.name} value={it.value} unit={it.unit} />

        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {datas.map(it => (
          <SensorCard name={it.temperature} />
        ))}
      </div>
    </div>
  )
}
