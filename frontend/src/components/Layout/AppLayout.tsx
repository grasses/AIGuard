
import { Layout } from 'antd';
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import TopBar from './TopBar';
import Sidebar from './Sidebar';

const { Content } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <TopBar />
      <Layout>
        <Sidebar collapsed={collapsed} />
        <Content style={{
          padding: 24,
          background: '#f5f5f5',
          overflow: 'auto',
          minHeight: 'calc(100vh - 56px)',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
