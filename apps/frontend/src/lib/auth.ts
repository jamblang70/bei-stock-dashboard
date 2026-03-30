import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { getServerSession as nextAuthGetServerSession } from "next-auth/next";
import api from "./api";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        try {
          const res = await api.post("/auth/login", {
            email: credentials.email,
            password: credentials.password,
          });
          const { access_token, refresh_token, user } = res.data;
          if (!access_token) return null;
          return { ...user, access_token, refresh_token };
        } catch {
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.access_token = (user as any).access_token;
        token.refresh_token = (user as any).refresh_token;
        token.id = user.id;
        token.name = user.name;
        token.email = user.email;
      }
      return token;
    },
    async session({ session, token }) {
      (session as any).access_token = token.access_token;
      if (session.user) {
        session.user.name = token.name as string;
        session.user.email = token.email as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 7 * 24 * 60 * 60, // 7 hari
  },
  secret: process.env.NEXTAUTH_SECRET,
};

/**
 * Wrapper getServerSession agar tidak perlu import authOptions di setiap server component.
 */
export async function getServerSession() {
  return nextAuthGetServerSession(authOptions);
}
