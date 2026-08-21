import { useEffect, useState } from "react";
import { getHospitals } from "../services/api";

function HospitalList() {
  const [hospitals, setHospitals] = useState([]);
  const [state, setState] = useState("");
  const [page, setPage] = useState(1);

  const limit = 20;

  useEffect(() => {
    getHospitals(page, limit, state).then(setHospitals);
  }, [page, state]);

  return (
    <div>
      <h2>CMS Hospitals</h2>

      <input
        type="text"
        placeholder="Filter per state"
        value={state}
        onChange={(e) => {
          setState(e.target.value);
          setPage(1);
        }}
      />

      {hospitals.map((hospital) => (
        <div key={hospital.facility_id}>
          <h3>{hospital.facility_name}</h3>
          <p>
            {hospital.city}, {hospital.state} - {hospital.zip_code}
          </p>
          <p>Rating: {hospital.overall_rating ?? "N/A"}</p>
        </div>
      ))}

      <button
        disabled={page === 1}
        onClick={() => setPage(page - 1)}
      >
        Previous
      </button>

      <span> Page {page} </span>

      <button
        disabled={hospitals.length < limit}
        onClick={() => setPage(page + 1)}
      >
        Next
      </button>
    </div>
  );
}

export default HospitalList;