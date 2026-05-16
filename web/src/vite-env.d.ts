/// <reference types="vite/client" />

interface Window {
  qt?: {
    webChannelTransport: unknown;
  };
}

declare const qt: Window["qt"];
