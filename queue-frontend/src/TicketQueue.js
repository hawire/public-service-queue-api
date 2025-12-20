import React, { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

function TicketQueue({ serviceId }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch all tickets for this service
  const fetchTickets = async () => {
    try {
      const res = await fetch(`${API_BASE}/tickets/?service=${serviceId}&ordering=number`);
      const data = await res.json();
      setTickets(data);
    } catch (err) {
      console.error("Error fetching tickets:", err);
    }
  };

  // Serve next pending ticket
  const serveNext = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/tickets/serve-next/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service: serviceId }),
      });
      await res.json();
      fetchTickets(); // refresh queue
    } catch (err) {
      console.error("Error serving next ticket:", err);
    }
    setLoading(false);
  };

  // Auto-refresh every 5 seconds
  useEffect(() => {
    fetchTickets();
    const interval = setInterval(fetchTickets, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ border: "1px solid #ccc", padding: "1rem", margin: "1rem", borderRadius: "8px" }}>
      <h2>Service {serviceId} Queue</h2>
      <button onClick={serveNext} disabled={loading} style={{ marginBottom: "1rem" }}>
        Serve Next
      </button>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {tickets.length === 0 && <li>No tickets</li>}
        {tickets.map((ticket) => (
          <li
            key={ticket.id}
            style={{
              fontWeight: ticket.status === "serving" ? "bold" : "normal",
              color: ticket.status === "serving" ? "green" : "black",
              padding: "0.5rem 0",
              borderBottom: "1px solid #eee",
            }}
          >
            Ticket #{ticket.number} - {ticket.status} - Citizen ID: {ticket.citizen}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default TicketQueue;
