import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Initialize Firebase only if it hasn't been initialized already
let app, auth, googleProvider;

if (firebaseConfig.apiKey) {
  app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
  auth = getAuth(app);
  googleProvider = new GoogleAuthProvider();
} else {
  // Mock during Next.js SSG build step or missing ENV vars
  app = {};
  const mockUser = { 
    uid: 'mock-user-123', 
    email: 'guest@intellicredit.com',
    getIdToken: async () => "mock.jwt.token"
  };
  auth = { 
    currentUser: mockUser,
    onAuthStateChanged: (cb) => { 
      typeof cb === 'function' && cb(mockUser); 
      return () => {}; 
    }, 
    signOut: async () => {} 
  };
  googleProvider = {};
}

export { app, auth, googleProvider };
