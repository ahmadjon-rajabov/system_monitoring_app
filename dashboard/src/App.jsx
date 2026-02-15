import { useState, useEffect, useRef } from 'react' 
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Activity, Cpu, Server, HardDrive, AlertTriangle, WifiOff, Clock } from 'lucide-react'

function App() {
  const [metrics, setMetrics] = useState([])
  const [prediction, setPrediction] = useState(null)
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [systemStatus, setSystemStatus] = useState("offline") 
  
  const lastTimestampRef = useRef(null)     // Keeps track of the last data 
  const stuckCounterRef = useRef(0)         // Counts how many times data was the same

  const fetchData = async () => {
    try {
      const [historyRes, predictRes] = await Promise.all([
        axios.get("http://127.0.0.1:8000/metrics?limit=30"),
        axios.get("http://127.0.0.1:8000/predict")
      ])

      // Timezone Proof
      const latestItem = historyRes.data.data[0] // API returns newest first
      
      if (latestItem) {
        const currentTimestamp = latestItem.timestamp
        
        if (currentTimestamp === lastTimestampRef.current) {
          // Data hasn't changed since last fetch
          stuckCounterRef.current += 1
        } else {
          // Data changed system is alive.
          stuckCounterRef.current = 0
          lastTimestampRef.current = currentTimestamp
        }

        // Data hasn't changed for 10+ seconds.
        if (stuckCounterRef.current > 5) {
           setSystemStatus("warning")
        } else {
           setSystemStatus("online")
        }
      }

      // Format data for chart
      const formattedData = historyRes.data.data.map(item => ({
        ...item,
        time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        cpu: item.cpu,
        memory: item.memory,
        disk: item.disk
      })).reverse()

      setMetrics(formattedData)
      setPrediction(predictRes.data)
      setError(null) 
      setLoading(false)

    } catch (err) {
      console.error("Fetch error:", err)
      setSystemStatus("offline")
      setError(err.message || "Unknown Connection Error")
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = () => {
    if (systemStatus === "online") return "#4ade80" 
    if (systemStatus === "warning") return "#facc15" 
    return "#ef4444" 
  }

  return (
    <div style={{ width: "100%", minHeight: "100vh", backgroundColor: "#1a1a1a", color: "white", padding: "2rem" }}>
      
      {/* HEADER */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem", borderBottom: "1px solid #333", paddingBottom: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Activity size={32} color={getStatusColor()} />
          <h1 style={{ margin: 0, fontSize: "1.8rem", letterSpacing: "-1px" }}>Eco-Pulse <span style={{color: "#666"}}>Command Center</span></h1>
        </div>
        
        {/* DYNAMIC STATUS BADGE */}
        <div style={{ display: "flex", gap: "1rem" }}>
             <span style={{ 
               padding: "0.5rem 1rem", 
               borderRadius: "20px", 
               backgroundColor: `${getStatusColor()}20`, 
               color: getStatusColor(),
               fontSize: "0.9rem", 
               fontWeight: "bold",
               display: "flex",
               alignItems: "center",
               gap: "8px",
               border: `1px solid ${getStatusColor()}`
             }}>
                {systemStatus === "online" && <Activity size={16}/>}
                {systemStatus === "warning" && <Clock size={16}/>}
                {systemStatus === "offline" && <WifiOff size={16}/>}
                
                {systemStatus === "online" && "System Online"}
                {systemStatus === "warning" && "Monitor Paused"}
                {systemStatus === "offline" && "System Offline"}
             </span>
        </div>
      </div>

      {/* ERROR: API DOWN */}
      {systemStatus === "offline" && (
        <div style={{ backgroundColor: "#450a0a", border: "1px solid #dc2626", borderRadius: "12px", padding: "2rem", textAlign: "center", marginTop: "4rem" }}>
          <WifiOff size={64} color="#fca5a5" style={{ marginBottom: "1rem" }} />
          <h2 style={{ color: "#fca5a5", marginTop: 0 }}>API Connection Failed</h2>
          <p style={{ color: "#fee2e2" }}>Check if Uvicorn is running.</p>
        </div>
      )}

      {/* WARNING: MONITOR DOWN */}
      {systemStatus === "warning" && (
        <div style={{ backgroundColor: "#422006", border: "1px solid #eab308", borderRadius: "12px", padding: "1rem", marginBottom: "2rem", display: "flex", alignItems: "center", gap: "1rem" }}>
          <AlertTriangle size={24} color="#facc15" />
          <div>
            <h3 style={{ margin: 0, color: "#facc15" }}>Data Stream Interrupted</h3>
            <p style={{ margin: 0, color: "#fde047", fontSize: "0.9rem" }}>
              The database has not received new data for over 10 seconds. Is <b>monitor.py</b> running?
            </p>
          </div>
        </div>
      )}

      {/* DASHBOARD CONTENT */}
      {(systemStatus === "online" || systemStatus === "warning") && !loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem", opacity: systemStatus === "warning" ? 0.5 : 1 }}>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.5rem" }}>
            <Card title="CPU Load" value={`${metrics[metrics.length - 1]?.cpu}%`} icon={<Cpu size={24} />} color="#f87171" />
            <Card title="Memory Usage" value={`${metrics[metrics.length - 1]?.memory}%`} icon={<Server size={24} />} color="#60a5fa" />
            <Card title="Disk Usage" value={`${metrics[metrics.length - 1]?.disk}%`} icon={<HardDrive size={24} />} color="#4ade80" />
            <Card title="AI Prediction" value={`${prediction?.predicted_cpu_load}%`} subtext={prediction?.status} icon={<Activity size={24} />} color="#c084fc" isPrediction={true} />
          </div>

          <div style={{ backgroundColor: "#262626", padding: "1.5rem", borderRadius: "12px", border: "1px solid #333", height: "500px" }}>
            <h3 style={{ marginTop: 0, marginBottom: "1.5rem", color: "#d4d4d4" }}>Live Resource Monitor</h3>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#404040" vertical={false} />
                <XAxis dataKey="time" stroke="#737373" tick={{fontSize: 12}} />
                <YAxis stroke="#737373" tick={{fontSize: 12}} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: "#171717", border: "1px solid #333" }} />
                <Legend />
                <Line type="monotone" dataKey="cpu" stroke="#f87171" strokeWidth={3} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="memory" stroke="#60a5fa" strokeWidth={3} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="disk" stroke="#4ade80" strokeWidth={3} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

        </div>
      )}
    </div>
  )
}

function Card({ title, value, icon, color, subtext, isPrediction }) {
  return (
    <div style={{ backgroundColor: "#262626", padding: "1.5rem", borderRadius: "12px", border: "1px solid #333", borderTop: `4px solid ${color}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
        <h4 style={{ margin: 0, color: "#a3a3a3" }}>{title}</h4>
        <div style={{ color: color }}>{icon}</div>
      </div>
      <span style={{ fontSize: "2.5rem", fontWeight: "bold", color: "#fff" }}>{value}</span>
      {subtext && <div style={{ marginTop: "8px", fontSize: "0.85rem", color: isPrediction ? "#c084fc" : "#737373" }}>{subtext}</div>}
    </div>
  )
}

export default App