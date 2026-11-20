import RoleDashboard from "@/components/RoleDashboard";

export default function LecturerPage() {
  return (
    <RoleDashboard
      expectedRole="lecturer"
      title="Lecturer workspace"
      description="Your authenticated lecturer workspace is ready for attendance-session controls."
    />
  );
}
