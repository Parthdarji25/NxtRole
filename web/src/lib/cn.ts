import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const merge = extendTailwindMerge({
  extend: {
    classGroups: {
      // Our own text utilities, so later classes replace earlier ones correctly.
      "font-weight": ["heading"],
    },
  },
});

/** Joins class names; when two Tailwind classes conflict, the later one wins. */
export function cn(...inputs: ClassValue[]): string {
  return merge(clsx(inputs));
}
