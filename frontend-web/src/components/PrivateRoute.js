import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const PrivateRoute = ({ children }) => {
  // Since we set user in useEffect initially, we might have a brief flash
  // Ideally AuthProvider should have a 'loading' state
  // But for now, we rely on token existence check in AuthProvider or here
  const token = localStorage.getItem("token");

  return token ? children : <Navigate to="/login" />;
};

export default PrivateRoute;
