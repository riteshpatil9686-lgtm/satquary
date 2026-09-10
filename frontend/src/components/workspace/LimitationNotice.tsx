import React from 'react';
import { MapPin } from 'lucide-react';

interface LimitationNoticeProps {
  message: string;
  icon?: boolean;
}

export const LimitationNotice: React.FC<LimitationNoticeProps> = ({ message, icon = true }) => (
  <div className="limitation-notice flex items-start gap-2.5 animate-fade-in">
    {icon && <MapPin size={13} className="text-limitation flex-shrink-0 mt-0.5" />}
    <p className="text-sm leading-relaxed">{message}</p>
  </div>
);
