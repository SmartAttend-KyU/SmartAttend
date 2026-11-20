import RoleDashboard from "@/components/RoleDashboard";

export default function AdminPage() {
  return (
    <RoleDashboard
      expectedRole="admin"
      title="Administrator workspace"
      description="Your authenticated administrator workspace is ready for system administration features."
    />
  );
}
