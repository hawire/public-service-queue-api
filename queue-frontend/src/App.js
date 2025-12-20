import React from "react";
import TicketQueue from "./TicketQueue";

function App() {
  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", fontFamily: "Arial, sans-serif" }}>
      <h1>Public Service Queue</h1>
      {/* Example: Service IDs 1 and 2 */}
      <TicketQueue serviceId={1} />
      <TicketQueue serviceId={2} />
    </div>
  );
}

export default App;
