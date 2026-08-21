import HospitalList from "./components/HospitalList";
import AIQuery from "./components/AIQuery";

function App() {
  return (
    <div>
      <h1>DataPulse</h1>
      <p>CMS Hospital Quality Data</p>
      <AIQuery />
      <HospitalList />
    </div>
  );
}

export default App;