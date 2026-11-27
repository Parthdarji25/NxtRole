import { defineConfig, globalIgnores } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier/flat";

export default defineConfig([
  ...nextCoreWebVitals,
  ...nextTypeScript,
  // Turns off style rules that would fight with Prettier.
  prettier,
  globalIgnores([
    ".next/**",
    "out/**",
    "next-env.d.ts",
    "playwright-report/**",
    "test-results/**",
    "coverage/**",
  ]),
]);
