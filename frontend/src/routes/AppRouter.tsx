// src/AppRouter.tsx (or wherever your router lives)
import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import {
  ConfirmEmail,
  Home,
  Login,
  SignUp,
  VerifyEmailPage,
  RecentVenture,
  Chat,
  NewVenture,
  AboutUs,
} from "../pages";
import Layout from "../features/Dashboard";
import ChatLayout from "../layout/chatLayout";

const isAuthenticated = (): boolean =>
  !!localStorage.getItem("sb_access_token");

// Helper: if logged in → redirect to /ventures, otherwise render the given component
const redirectIfAuth = (component: React.ReactElement) =>
  isAuthenticated() ? <Navigate to="/ventures" replace /> : component;

// PrivateRoute stays the same
interface PrivateRouteProps {
  children: React.ReactElement;
}
const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) =>
  isAuthenticated() ? children : <Navigate to="/login" replace />;

const router = createBrowserRouter([
  {
    path: "/",
    children: [
      {
        path: "auth/confirm",
        element: <ConfirmEmail />,
        errorElement: <ConfirmEmail />,
      },
      {
        path: "verify-email",
        element: redirectIfAuth(<VerifyEmailPage />),
        errorElement: <VerifyEmailPage />,
      },
      {
        path: "signup",
        element: redirectIfAuth(<SignUp />),
        errorElement: <SignUp />,
      },
      {
        path: "login",
        element: redirectIfAuth(<Login />),
        errorElement: <Login />,
      },
      {
        path: "/",
        element: <Layout />,
        children: [
          {
            index: true,
            element: <Home />,
          },
          {
            path: "ventures",
            element: (
              <PrivateRoute>
                <ChatLayout />
              </PrivateRoute>
            ),
            children: [
              {
                index: true,
                element: <RecentVenture />,
              },
              {
                path: "new-session",
                element: <NewVenture />,
              },
              {
                path: ":id",
                element: <Chat />,
              },
            ],
          },
          {
            path: "/about",
            element: <AboutUs />,
            errorElement: <AboutUs />,
          },
        ],
      },
    ],
  },
]);

export default router;
