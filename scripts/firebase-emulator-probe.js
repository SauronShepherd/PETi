const required = {
  auth: process.env.FIREBASE_AUTH_EMULATOR_HOST,
  firestore: process.env.FIRESTORE_EMULATOR_HOST,
  storage: process.env.FIREBASE_STORAGE_EMULATOR_HOST,
};

const missing = Object.entries(required)
  .filter(([, value]) => !value)
  .map(([name]) => name);

if (missing.length > 0) {
  throw new Error(`Missing emulator endpoints: ${missing.join(", ")}`);
}

console.log(`FIREBASE_EMULATOR_ENDPOINTS_READY ${JSON.stringify(required)}`);
