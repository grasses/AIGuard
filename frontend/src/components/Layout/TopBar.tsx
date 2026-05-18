
import { Layout, Badge, Avatar, Dropdown, Space, Tag, Typography } from 'antd';
import {
  BellOutlined, UserOutlined, LogoutOutlined, KeyOutlined,
  SettingOutlined, DollarOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/authStore';
import { useNotificationStore } from '../../stores/notificationStore';
import { useEffect } from 'react';
import { alertsApi } from '../../api/alerts';

const { Header } = Layout;
const { Text } = Typography;

export default function TopBar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, logout, isAdmin } = useAuthStore();
  const { unreadCount, fetchUnreadCount } = useNotificationStore();

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: t('nav.profile') },
    { key: 'apikeys', icon: <KeyOutlined />, label: t('nav.apiKeys') },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: t('nav.logout'), danger: true },
  ];

  const adminMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: t('nav.profile') },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: t('nav.logout'), danger: true },
  ];

  return (
    <Header style={{
      background: '#fff',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      borderBottom: '1px solid #f0f0f0',
      height: 56,
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Left */}
      <Space>
        <Text strong style={{ fontSize: 18, color: '#1677ff' }}>
          🛡️ {t('app.title')}
        </Text>
      </Space>

      {/* Right */}
      <Space size="middle">
        {user && user.role === 'user' && (
          <Tag
            color="blue"
            style={{ cursor: 'pointer' }}
            onClick={() => navigate('/user/billing')}
          >
            💰 {user.balance.toLocaleString()} {t('billing.points')}
          </Tag>
        )}

        <Badge count={unreadCount} size="small">
          <BellOutlined
            style={{ fontSize: 18, cursor: 'pointer' }}
            onClick={() => navigate(isAdmin() ? '/admin/alerts' : '/user/alerts')}
          />
        </Badge>

        <Dropdown
          menu={{
            items: isAdmin() ? adminMenuItems : userMenuItems,
            onClick: ({ key }) => {
              if (key === 'logout') handleLogout();
              if (key === 'apikeys') navigate(isAdmin() ? '/admin/api-keys' : '/user/api-keys');
            },
          }}
        >
          <Space style={{ cursor: 'pointer' }}>
            <Avatar size={28} icon={<UserOutlined />} />
            <Text>{user?.username}</Text>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
}
