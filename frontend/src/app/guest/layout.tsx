import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Cổng Ứng Viên | Paraline Vietnam',
  description: 'Tìm hiểu về cơ hội việc làm tại Paraline Vietnam. Hỏi AI về vị trí tuyển dụng, quy trình phỏng vấn và văn hóa công ty.',
};

export default function GuestLayout({ children }: { children: React.ReactNode }) {
  return children;
}
