import { waitForElement } from "../../syscore/dom_utils";
import { staticPortalBridge } from "./PortalBridge";


waitForElement('#global', (el) => {
    staticPortalBridge.registerContainer("global", el);
})
