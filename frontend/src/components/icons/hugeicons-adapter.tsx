import React from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import {
  AiMagicIcon,
  Alert02Icon,
  Analytics01Icon,
  ArrowDown01Icon,
  ArrowDownRight01Icon,
  ArrowLeft01Icon,
  ArrowRight01Icon,
  ArrowUp01Icon,
  ArrowUpRight01Icon,
  Award01Icon,
  Book02Icon,
  Building01Icon,
  BulbIcon,
  Calendar01Icon,
  Calendar03Icon,
  Cancel01Icon,
  CancelCircleIcon,
  CheckmarkCircle01Icon,
  CheckmarkCircle02Icon,
  CheckmarkSquare01Icon,
  ChevronDownIcon,
  ChevronRightIcon,
  CircleIcon,
  ClipboardListIcon,
  Clock01Icon,
  Clock02Icon,
  CodeIcon,
  CodeSquareIcon,
  Copy01Icon,
  CpuIcon,
  Csv01Icon,
  DashboardSquare01Icon,
  DatabaseIcon,
  Delete02Icon,
  Download01Icon,
  Edit01Icon,
  Edit02Icon,
  File01Icon,
  FileCheckIcon,
  FileCodeIcon,
  FilterIcon,
  FireIcon,
  FlashIcon,
  HardDriveIcon,
  InformationCircleIcon,
  Key01Icon,
  LaptopIcon,
  Layers01Icon,
  Loading01Icon,
  Location01Icon,
  LockIcon,
  Logout01Icon,
  Mail01Icon,
  Maximize01Icon,
  Menu01Icon,
  Message01Icon,
  Minimize01Icon,
  MonitorIcon,
  Moon02Icon,
  MoreHorizontalIcon,
  Mortarboard01Icon,
  Notification01Icon,
  Notification02Icon,
  PencilEdit01Icon,
  PieChartIcon,
  PlayIcon,
  PlusSignIcon,
  PrinterIcon,
  RefreshIcon,
  RotateCcwIcon,
  Search01Icon,
  SentIcon,
  Settings01Icon,
  Settings02Icon,
  Shield01Icon,
  ShieldAlertIcon,
  Sun02Icon,
  Target01Icon,
  Task01Icon,
  TerminalIcon,
  Tick02Icon,
  TradeUpIcon,
  TriangleAlertIcon,
  TrophyIcon,
  UniversityIcon,
  UserAccountIcon,
  UserAdd01Icon,
  UserCircleIcon,
  UserGroupIcon,
  UserRemove01Icon,
  UserSettings01Icon,
  ViewIcon,
  ViewOffIcon
} from '@hugeicons/core-free-icons';

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  strokeWidth?: number;
  className?: string;
  color?: string;
}

export type LucideIcon = React.ForwardRefExoticComponent<IconProps & React.RefAttributes<SVGSVGElement>>;

export const createHugeIcon = (iconData: any, displayName?: string): LucideIcon => {
  const Comp = React.forwardRef<SVGSVGElement, IconProps>(
    ({ size = 24, strokeWidth = 1.5, className = '', color = 'currentColor', ...rest }, ref) => (
      <HugeiconsIcon
        ref={ref}
        icon={iconData}
        size={size}
        strokeWidth={strokeWidth}
        color={color}
        className={className}
        {...(rest as any)}
      />
    )
  );
  if (displayName) Comp.displayName = displayName;
  return Comp;
};

export const createLucideIcon = (iconName: string, iconNode: any) => {
  return createHugeIcon(iconNode, iconName);
};

export const AlertCircle = createHugeIcon(Alert02Icon, 'AlertCircle');
export const AlertTriangle = createHugeIcon(TriangleAlertIcon, 'AlertTriangle');
export const ArrowDown = createHugeIcon(ArrowDown01Icon, 'ArrowDown');
export const ArrowDownRight = createHugeIcon(ArrowDownRight01Icon, 'ArrowDownRight');
export const ArrowLeft = createHugeIcon(ArrowLeft01Icon, 'ArrowLeft');
export const ArrowRight = createHugeIcon(ArrowRight01Icon, 'ArrowRight');
export const ArrowUp = createHugeIcon(ArrowUp01Icon, 'ArrowUp');
export const ArrowUpRight = createHugeIcon(ArrowUpRight01Icon, 'ArrowUpRight');
export const Award = createHugeIcon(Award01Icon, 'Award');
export const BarChart3 = createHugeIcon(Analytics01Icon, 'BarChart3');
export const Bell = createHugeIcon(Notification02Icon, 'Bell');
export const BellRing = createHugeIcon(Notification01Icon, 'BellRing');
export const BookOpen = createHugeIcon(Book02Icon, 'BookOpen');
export const Building = createHugeIcon(Building01Icon, 'Building');
export const Calendar = createHugeIcon(Calendar03Icon, 'Calendar');
export const CalendarCheck = createHugeIcon(Calendar01Icon, 'CalendarCheck');
export const Check = createHugeIcon(Tick02Icon, 'Check');
export const CheckCircle = createHugeIcon(CheckmarkCircle01Icon, 'CheckCircle');
export const CheckCircle2 = createHugeIcon(CheckmarkCircle02Icon, 'CheckCircle2');
export const CheckSquare = createHugeIcon(CheckmarkSquare01Icon, 'CheckSquare');
export const ChevronDown = createHugeIcon(ChevronDownIcon, 'ChevronDown');
export const ChevronRight = createHugeIcon(ChevronRightIcon, 'ChevronRight');
export const Circle = createHugeIcon(CircleIcon, 'Circle');
export const ClipboardList = createHugeIcon(ClipboardListIcon, 'ClipboardList');
export const Clock = createHugeIcon(Clock01Icon, 'Clock');
export const Clock3 = createHugeIcon(Clock02Icon, 'Clock3');
export const Code = createHugeIcon(CodeIcon, 'Code');
export const Code2 = createHugeIcon(CodeSquareIcon, 'Code2');
export const Copy = createHugeIcon(Copy01Icon, 'Copy');
export const Cpu = createHugeIcon(CpuIcon, 'Cpu');
export const Database = createHugeIcon(DatabaseIcon, 'Database');
export const Download = createHugeIcon(Download01Icon, 'Download');
export const Edit = createHugeIcon(Edit01Icon, 'Edit');
export const Edit3 = createHugeIcon(Edit02Icon, 'Edit3');
export const Eye = createHugeIcon(ViewIcon, 'Eye');
export const EyeOff = createHugeIcon(ViewOffIcon, 'EyeOff');
export const FileCheck2 = createHugeIcon(FileCheckIcon, 'FileCheck2');
export const FileCode = createHugeIcon(FileCodeIcon, 'FileCode');
export const FileCode2 = createHugeIcon(FileCodeIcon, 'FileCode2');
export const FileSpreadsheet = createHugeIcon(Csv01Icon, 'FileSpreadsheet');
export const FileText = createHugeIcon(File01Icon, 'FileText');
export const Filter = createHugeIcon(FilterIcon, 'Filter');
export const Flame = createHugeIcon(FireIcon, 'Flame');
export const GraduationCap = createHugeIcon(Mortarboard01Icon, 'GraduationCap');
export const HardDrive = createHugeIcon(HardDriveIcon, 'HardDrive');
export const Info = createHugeIcon(InformationCircleIcon, 'Info');
export const KeyRound = createHugeIcon(Key01Icon, 'KeyRound');
export const Laptop = createHugeIcon(LaptopIcon, 'Laptop');
export const Layers = createHugeIcon(Layers01Icon, 'Layers');
export const LayoutDashboard = createHugeIcon(DashboardSquare01Icon, 'LayoutDashboard');
export const Lightbulb = createHugeIcon(BulbIcon, 'Lightbulb');
export const LineChart = createHugeIcon(Analytics01Icon, 'LineChart');
export const ListOrdered = createHugeIcon(Task01Icon, 'ListOrdered');
export const LoaderCircle = createHugeIcon(Loading01Icon, 'LoaderCircle');
export const LockKeyhole = createHugeIcon(LockIcon, 'LockKeyhole');
export const LogOut = createHugeIcon(Logout01Icon, 'LogOut');
export const Mail = createHugeIcon(Mail01Icon, 'Mail');
export const MapPin = createHugeIcon(Location01Icon, 'MapPin');
export const Maximize2 = createHugeIcon(Maximize01Icon, 'Maximize2');
export const Menu = createHugeIcon(Menu01Icon, 'Menu');
export const MessageSquareText = createHugeIcon(Message01Icon, 'MessageSquareText');
export const Minimize2 = createHugeIcon(Minimize01Icon, 'Minimize2');
export const Monitor = createHugeIcon(MonitorIcon, 'Monitor');
export const Moon = createHugeIcon(Moon02Icon, 'Moon');
export const MoreHorizontal = createHugeIcon(MoreHorizontalIcon, 'MoreHorizontal');
export const Pencil = createHugeIcon(PencilEdit01Icon, 'Pencil');
export const PieChart = createHugeIcon(PieChartIcon, 'PieChart');
export const Play = createHugeIcon(PlayIcon, 'Play');
export const Plus = createHugeIcon(PlusSignIcon, 'Plus');
export const Printer = createHugeIcon(PrinterIcon, 'Printer');
export const RefreshCw = createHugeIcon(RefreshIcon, 'RefreshCw');
export const RotateCcw = createHugeIcon(RotateCcwIcon, 'RotateCcw');
export const School = createHugeIcon(UniversityIcon, 'School');
export const Search = createHugeIcon(Search01Icon, 'Search');
export const Send = createHugeIcon(SentIcon, 'Send');
export const Settings = createHugeIcon(Settings01Icon, 'Settings');
export const Settings2 = createHugeIcon(Settings02Icon, 'Settings2');
export const Shield = createHugeIcon(Shield01Icon, 'Shield');
export const ShieldAlert = createHugeIcon(ShieldAlertIcon, 'ShieldAlert');
export const ShieldCheck = createHugeIcon(Shield01Icon, 'ShieldCheck');
export const Sparkles = createHugeIcon(AiMagicIcon, 'Sparkles');
export const Sun = createHugeIcon(Sun02Icon, 'Sun');
export const Target = createHugeIcon(Target01Icon, 'Target');
export const Terminal = createHugeIcon(TerminalIcon, 'Terminal');
export const Trash2 = createHugeIcon(Delete02Icon, 'Trash2');
export const TrendingUp = createHugeIcon(TradeUpIcon, 'TrendingUp');
export const Trophy = createHugeIcon(TrophyIcon, 'Trophy');
export const User = createHugeIcon(UserAccountIcon, 'User');
export const UserCog = createHugeIcon(UserSettings01Icon, 'UserCog');
export const UserPlus = createHugeIcon(UserAdd01Icon, 'UserPlus');
export const UserRound = createHugeIcon(UserCircleIcon, 'UserRound');
export const UserRoundMinus = createHugeIcon(UserRemove01Icon, 'UserRoundMinus');
export const Users = createHugeIcon(UserGroupIcon, 'Users');
export const X = createHugeIcon(Cancel01Icon, 'X');
export const XCircle = createHugeIcon(CancelCircleIcon, 'XCircle');
export const Zap = createHugeIcon(FlashIcon, 'Zap');

export default {
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  ArrowDownRight,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowUpRight,
  Award,
  BarChart3,
  Bell,
  BellRing,
  BookOpen,
  Building,
  Calendar,
  CalendarCheck,
  Check,
  CheckCircle,
  CheckCircle2,
  CheckSquare,
  ChevronDown,
  ChevronRight,
  Circle,
  ClipboardList,
  Clock,
  Clock3,
  Code,
  Code2,
  Copy,
  Cpu,
  Database,
  Download,
  Edit,
  Edit3,
  Eye,
  EyeOff,
  FileCheck2,
  FileCode,
  FileCode2,
  FileSpreadsheet,
  FileText,
  Filter,
  Flame,
  GraduationCap,
  HardDrive,
  Info,
  KeyRound,
  Laptop,
  Layers,
  LayoutDashboard,
  Lightbulb,
  LineChart,
  ListOrdered,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Mail,
  MapPin,
  Maximize2,
  Menu,
  MessageSquareText,
  Minimize2,
  Monitor,
  Moon,
  MoreHorizontal,
  Pencil,
  PieChart,
  Play,
  Plus,
  Printer,
  RefreshCw,
  RotateCcw,
  School,
  Search,
  Send,
  Settings,
  Settings2,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Sun,
  Target,
  Terminal,
  Trash2,
  TrendingUp,
  Trophy,
  User,
  UserCog,
  UserPlus,
  UserRound,
  UserRoundMinus,
  Users,
  X,
  XCircle,
  Zap,
};
