
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined, DatabaseOutlined, SafetyOutlined,
  ApartmentOutlined, DollarOutlined, AlertOutlined,
  FileTextOutlined, TeamOutlined, SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/authStore';
import type { MenuProps } from 'antd';

const { Sider } = Layout;

export default function Sidebar({ collapsed }: { collapsed: boolean }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAdmin, isSuperAdmin } = useAuthStore();
  const admin = isAdmin();

  const userItems: MenuProps['items'] = [
    { key: `/${admin ? 'admin' : 'user'}/dashboard`, icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: `/${admin ? 'admin' : 'user'}/assets`, icon: <DatabaseOutlined />, label: t('nav.assets') },
    { key: `/${admin ? 'admin' : 'user'}/guardrails`, icon: <SafetyOutlined />, label: t('nav.guardrails') },
    { key: `/${admin ? 'admin' : 'user'}/traffic-configs`, icon: <ApartmentOutlined />, label: t('nav.trafficConfigs') },
    { key: `/${admin ? 'admin' : 'user'}/billing`, icon: <DollarOutlined />, label: t('nav.billing') },
    { key: `/${admin ? 'admin' : 'user'}/alerts`, icon: <AlertOutlined />, label: t('nav.alerts') },
    { key: `/${admin ? 'admin' : 'user'}/logs`, icon: <FileTextOutlined />, label: t('nav.logs') },
  ];

  const adminItems: MenuProps['items'] = [
    ...(admin ? [
      { key: '/admin/users', icon: <TeamOutlined />, label: t('nav.userManagement') },
    ] : []),
    ...(isSuperAdmin() ? [
      { key: '/admin/settings', icon: <SettingOutlined />, label: t('nav.settings') },
    ] : []),
  ];

  const allItems = [...userItems, ...adminItems];

  // Determine selected key
  const pathParts = location.pathname.split('/');
  const selectedKey = '/' + pathParts.slice(1, 3).join('/');

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      width={220}
      style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}
    >
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        items={allItems}
        onClick={({ key }) => navigate(key)}
        style={{ borderRight: 0, marginTop: 8 }}
      />
    </Sider>
  );
}
