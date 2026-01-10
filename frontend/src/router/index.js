import { createBrowserRouter } from "react-router-dom";
import App from "../App";
import AllDashasPage from "../components/all-dashas-page";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/all-dashas",
    element: <AllDashasPage />,
  },
]);

export default router;