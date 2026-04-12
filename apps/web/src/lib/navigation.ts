export type NavigationItem = {
  href: string;
  label: string;
  shortLabel: string;
};


export const dashboardNavigation: NavigationItem[] = [
  {
    href: "/chat",
    label: "Chat",
    shortLabel: "01",
  },
  {
    href: "/documents",
    label: "Documents",
    shortLabel: "02",
  },
  {
    href: "/runs",
    label: "Runs",
    shortLabel: "03",
  },
  {
    href: "/settings",
    label: "Settings",
    shortLabel: "04",
  },
];
