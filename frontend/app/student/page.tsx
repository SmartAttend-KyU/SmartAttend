import RoleDashboard from "@/components/RoleDashboard";

export default function StudentPage() {
  return (
    <RoleDashboard
      expectedRole="student"
      title="Student workspace"
      description="Your authenticated student workspace is ready for attendance verification."
    />
  );
}
