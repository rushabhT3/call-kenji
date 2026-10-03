import "./styles/base.css";
import "./ui/ui.css";
import "./landing/landing.css";
import "./xray/xray.css";
import "./aftercall/aftercall.css";
import { StrictMode, Suspense, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App.tsx";
import { pageForPath, type Page } from "./pages.ts";
import { LazyPitchPage } from "./pitch/LazyPitchPage.tsx";
import { LazyShowcasePage } from "./showcase/LazyShowcasePage.tsx";
import { LazyTrailerPage } from "./trailer/LazyTrailerPage.tsx";

const PAGES: Record<Page, ReactNode> = {
  call: <App />,
  showcase: <LazyShowcasePage />,
  pitch: <LazyPitchPage />,
  trailer: <LazyTrailerPage />,
};

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <Suspense fallback={null}>{PAGES[pageForPath(window.location.pathname)]}</Suspense>
  </StrictMode>,
);
