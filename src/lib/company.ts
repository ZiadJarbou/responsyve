export const email = "info@responsyve.co";

// Set these back to true to restore the preserved product section and slides.
export const siteVisibility = {
  selectedWork: false,
  productSlides: false,
};

export const products = [
  {
    name: "KarCast",
    href: "https://karcast.app",
    host: "karcast.app",
    line: "Android Auto on your car screen",
    body: "Bring Android Auto from your phone to a compatible car browser over local Wi-Fi. No extra hardware.",
    meta: "AED 5 per month",
  },
  {
    name: "LeafletAI",
    href: "https://leafletai.ai",
    host: "leafletai.ai",
    line: "Create leaflets that sell",
    body: "Responsyve’s product for promotional leaflets — the short piece a business uses when it needs someone to notice and act.",
    meta: "Live product",
  },
] as const;

export const activities = [
  {
    title: "E-commerce",
    body: "Online selling: stores, catalogues, and the systems that carry an order through.",
  },
  {
    title: "Systems software and applications",
    body: "Designing the structure and content of, and/or writing the computer code necessary to create and implement systems software and application (including updates and patches), database and webpages.",
  },
  {
    title: "Web design",
    body: "The structure, content, and look of websites and pages.",
  },
  {
    title: "Digital marketing",
    body: "Campaigns that reach people in the places they already give their attention.",
  },
  {
    title: "Branding services",
    body: "Names, marks, and the visual system a product is recognised by.",
  },
] as const;

export const premises = [
  { label: "Premises no.", value: "Business Centre" },
  { label: "Floor number", value: "3" },
  { label: "Building name", value: "A3" },
  { label: "Area name", value: "Business Park" },
  { label: "City", value: "Dubai" },
  { label: "Country", value: "United Arab Emirates" },
] as const;

export const premisesPlain = premises.map((row) => `${row.label} ${row.value}`).join("\n");
