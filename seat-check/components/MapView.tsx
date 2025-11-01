// seat-check/components/MapView.tsx
import { Platform } from "react-native";
import Web from "./MapView.web";
import Native from "./MapView.native";

export default Platform.OS === "web" ? Web : Native;
