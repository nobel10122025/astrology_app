import { configureStore } from "@reduxjs/toolkit";
import userReducer from "./user/reducer";

const store = configureStore({
  reducer: {
    user: userReducer,
  },
});

export default store;