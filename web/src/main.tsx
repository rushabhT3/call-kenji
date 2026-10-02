import "./styles/base.css";
import "./ui/ui.css";
import "./landing/landing.css";
import "./xray/xray.css";
import "./aftercall/aftercall.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App.tsx";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
