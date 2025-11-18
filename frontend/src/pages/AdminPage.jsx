import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    WifiIcon,
    UserGroupIcon,
    ShieldCheckIcon,
    CogIcon,
    PlusIcon,
    TrashIcon,
    EyeIcon,
    EyeSlashIcon,
    QrCodeIcon,
    ClockIcon,
    ChartBarIcon,
    KeyIcon,
    DocumentTextIcon,
    XMarkIcon,
    DocumentChartBarIcon
} from '@heroicons/react/24/outline';


const AdminPage = () => {
    const [activeTab, setActiveTab] = useState('networks');
    const [loading, setLoading] = useState(false);
    const [devices, setDevices] = useState([]);
    const [networks, setNetworks] = useState([]);
    const [users, setUsers] = useState([]);
    const [accessCodes, setAccessCodes] = useState([]);
    const [deviceHistory, setDeviceHistory] = useState([]);
    const [reports, setReports] = useState([]);

    const [newNetwork, setNewNetwork] = useState({
        name: "",
        ssid: "",
        security: "wpa2",
        band: "2.4GHz",
        password: "",
        vlan: "",
        maxClients: 50
    });

    const [newUser, setNewUser] = useState({
        email: "",
        role: "technician",
        networks: [],
        permissions: []
    });

    const [newAccessCode, setNewAccessCode] = useState({
        network: "",
        maxUses: 10,
        expires: "",
        description: ""
    });

    // Load data on component mount
    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            // Load all initial data in parallel
            await Promise.all([
                loadNetworks(),
                loadUsers(),
                loadAccessCodes(),
                loadDeviceHistory(),
                loadReports()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadNetworks = async () => {
        const response = await api.getNetworks();
        setNetworks(response.data);
    };

    const loadUsers = async () => {
        const response = await api.getUsers();
        setUsers(response.data);
    };

    const loadAccessCodes = async () => {
        // Mock data for demonstration
        setAccessCodes([
            {
                id: 1,
                code: "GUEST-2024-ABC123",
                network: "Guest Network",
                uses: 15,
                maxUses: 50,
                expires: "2024-12-31",
                status: "active",
                created: "2024-01-15"
            }
        ]);
    };

    const loadDeviceHistory = async () => {
        const response = await api.getDeviceHistory();
        setDeviceHistory(response.data);
    };

    const loadReports = async () => {
        const response = await api.getReports();
        setReports(response.data);
    };

    // Network Management
    const handleCreateNetwork = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await api.createNetwork(newNetwork);
            setNetworks(prev => [...prev, { ...response.data, id: Date.now(), clients: 0, status: 'active' }]);
            setNewNetwork({ name: "", ssid: "", security: "wpa2", band: "2.4GHz", password: "", vlan: "", maxClients: 50 });
            document.getElementById('create_network_modal').close();
        } catch (error) {
            console.error('Error creating network:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteNetwork = async (networkId) => {
        if (window.confirm('Are you sure you want to delete this network?')) {
            setLoading(true);
            try {
                // await api.deleteNetwork(networkId);
                setNetworks(prev => prev.filter(network => network.id !== networkId));
            } catch (error) {
                console.error('Error deleting network:', error);
            } finally {
                setLoading(false);
            }
        }
    };

    // User Management
    const handleCreateUser = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await api.createUser(newUser);
            setUsers(prev => [...prev, { ...response.data, id: Date.now(), status: 'active', lastLogin: 'Never' }]);
            setNewUser({ email: "", role: "technician", networks: [], permissions: [] });
            document.getElementById('create_user_modal').close();
        } catch (error) {
            console.error('Error creating user:', error);
        } finally {
            setLoading(false);
        }
    };

    // Access Code Management
    const handleGenerateAccessCode = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await api.generateAccessCode(newAccessCode);
            setAccessCodes(prev => [...prev, { ...response.data, id: Date.now(), uses: 0, status: 'active' }]);
            setNewAccessCode({ network: "", maxUses: 10, expires: "", description: "" });
            document.getElementById('create_code_modal').close();
        } catch (error) {
            console.error('Error generating access code:', error);
        } finally {
            setLoading(false);
        }
    };

    // Tab Components
    const NetworksTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Network Management</h2>
                <button
                    onClick={() => document.getElementById('create_network_modal').showModal()}
                    className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>Create Network</span>
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {networks.map(network => (
                    <div key={network.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50 hover:shadow-xl transition-all duration-300">
                        <div className="flex items-center justify-between mb-4">
                            <WifiIcon className="w-8 h-8 text-blue-500" />
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${network.status === 'active'
                                    ? 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400'
                                    : 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-400'
                                }`}>
                                {network.status}
                            </span>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{network.name}</h3>
                        <p className="text-gray-600 dark:text-gray-300 text-sm mb-1">SSID: {network.ssid}</p>
                        <p className="text-gray-600 dark:text-gray-300 text-sm mb-1">Security: {network.security.toUpperCase()}</p>
                        <p className="text-gray-600 dark:text-gray-300 text-sm mb-3">
                            <span className="font-semibold text-blue-600 dark:text-blue-400">{network.clients}</span> connected devices
                        </p>
                        <div className="flex space-x-2">
                            <button className="flex-1 bg-gray-100 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                                Edit
                            </button>
                            <button
                                onClick={() => handleDeleteNetwork(network.id)}
                                className="flex-1 bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 py-2 rounded-lg text-sm hover:bg-red-200 dark:hover:bg-red-500/30 transition-colors"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const UsersTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">User Management</h2>
                <button
                    onClick={() => document.getElementById('create_user_modal').showModal()}
                    className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>Add User</span>
                </button>
            </div>

            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg overflow-hidden border border-white/20 dark:border-gray-700/50">
                <table className="w-full">
                    <thead className="bg-gray-50/80 dark:bg-gray-700/80">
                        <tr>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">User</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Role</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Status</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Last Login</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200/50 dark:divide-gray-600/50">
                        {users.map(user => (
                            <tr key={user.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/50 transition-colors">
                                <td className="px-6 py-4">
                                    <div className="text-sm font-medium text-gray-900 dark:text-white">{user.email}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${user.role === 'administrator'
                                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-500/20 dark:text-purple-400'
                                            : 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-400'
                                        }`}>
                                        {user.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${user.status === 'active'
                                            ? 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400'
                                            : 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-400'
                                        }`}>
                                        {user.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{user.lastLogin}</td>
                                <td className="px-6 py-4">
                                    <div className="flex space-x-3">
                                        <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors">
                                            Edit Role
                                        </button>
                                        <button className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 transition-colors">
                                            Remove
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const AccessCodesTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Access Codes</h2>
                <button
                    onClick={() => document.getElementById('create_code_modal').showModal()}
                    className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                    <KeyIcon className="w-5 h-5" />
                    <span>Generate Code</span>
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {accessCodes.map((code) => (
                    <div key={code.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50 hover:shadow-xl transition-all duration-300">
                        <div className="flex items-center justify-between mb-4">
                            <KeyIcon className="w-8 h-8 text-green-500" />
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${code.status === 'active'
                                    ? 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400'
                                    : 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-400'
                                }`}>
                                {code.status}
                            </span>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 font-mono bg-gray-100 dark:bg-gray-700/50 p-2 rounded">
                            {code.code}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-300 text-sm mb-1">Network: {code.network}</p>
                        <p className="text-gray-600 dark:text-gray-300 text-sm mb-1">
                            Uses: <span className="font-semibold text-blue-600 dark:text-blue-400">{code.uses}/{code.maxUses}</span>
                        </p>
                        <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">Expires: {code.expires}</p>
                        <div className="flex space-x-2">
                            <button className="flex-1 bg-gray-100 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center justify-center">
                                <QrCodeIcon className="w-4 h-4 mr-1" />
                                QR Code
                            </button>
                            <button className="flex-1 bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 py-2 rounded-lg text-sm hover:bg-red-200 dark:hover:bg-red-500/30 transition-colors">
                                Revoke
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const DeviceHistoryTab = () => (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Device Connection History</h2>
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50">
                <p className="text-gray-600 dark:text-gray-300 text-center py-8">
                    Device history analytics and connection logs will be displayed here.
                </p>
            </div>
        </div>
    );

    const ReportsTab = () => (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Network Reports</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50">
                    <DocumentChartBarIcon className="w-12 h-12 text-blue-500 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Usage Statistics</h3>
                    <p className="text-gray-600 dark:text-gray-300 text-sm">Bandwidth usage and connection trends</p>
                </div>
                <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50">
                    <ShieldCheckIcon className="w-12 h-12 text-green-500 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Security Audit</h3>
                    <p className="text-gray-600 dark:text-gray-300 text-sm">Security events and access patterns</p>
                </div>
            </div>
        </div>
    );

    const tabs = [
        { id: 'networks', name: 'Networks', icon: WifiIcon, component: NetworksTab },
        { id: 'users', name: 'Users', icon: UserGroupIcon, component: UsersTab },
        { id: 'access-codes', name: 'Access Codes', icon: KeyIcon, component: AccessCodesTab },
        { id: 'device-history', name: 'Device History', icon: ClockIcon, component: DeviceHistoryTab },
        { id: 'reports', name: 'Reports', icon: ChartBarIcon, component: ReportsTab }
    ];

    const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-gray-900 dark:via-blue-900/20 dark:to-purple-900/20 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Network Administration
                    </h1>
                    <p className="text-gray-600 dark:text-gray-300">
                        Manage networks, users, and access controls
                    </p>
                </div>

                {/* Tab Navigation */}
                <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg mb-6 border border-white/20 dark:border-gray-700/50">
                    <div className="border-b border-gray-200/50 dark:border-gray-700/50">
                        <nav className="-mb-px flex space-x-8 px-6 overflow-x-auto">
                            {tabs.map(tab => {
                                const Icon = tab.icon;
                                return (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-all duration-300 ${activeTab === tab.id
                                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                                            }`}
                                    >
                                        <Icon className="w-5 h-5" />
                                        <span>{tab.name}</span>
                                    </button>
                                );
                            })}
                        </nav>
                    </div>

                    {/* Tab Content */}
                    <div className="p-6">
                        {loading ? (
                            <div className="flex justify-center items-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                            </div>
                        ) : (
                            ActiveComponent && <ActiveComponent />
                        )}
                    </div>
                </div>
            </div>

            {/* Create Network Modal */}
            <CreateNetworkModal
                newNetwork={newNetwork}
                setNewNetwork={setNewNetwork}
                handleCreateNetwork={handleCreateNetwork}
                loading={loading}
            />

            {/* Create User Modal */}
            <CreateUserModal
                newUser={newUser}
                setNewUser={setNewUser}
                handleCreateUser={handleCreateUser}
                loading={loading}
                networks={networks}
            />

            {/* Create Access Code Modal */}
            <CreateAccessCodeModal
                newAccessCode={newAccessCode}
                setNewAccessCode={setNewAccessCode}
                handleGenerateAccessCode={handleGenerateAccessCode}
                loading={loading}
                networks={networks}
            />
        </div>
    );
};

// Modal Components
const CreateNetworkModal = ({ newNetwork, setNewNetwork, handleCreateNetwork, loading }) => (
    <dialog id="create_network_modal" className="modal">
        <div className="modal-box bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 max-w-2xl">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Create New Network</h3>
                <button onClick={() => document.getElementById('create_network_modal').close()} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    <XMarkIcon className="w-6 h-6" />
                </button>
            </div>
            <form onSubmit={handleCreateNetwork} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Network Name</label>
                        <input
                            type="text"
                            required
                            value={newNetwork.name}
                            onChange={(e) => setNewNetwork({ ...newNetwork, name: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="Office WiFi"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">SSID</label>
                        <input
                            type="text"
                            required
                            value={newNetwork.ssid}
                            onChange={(e) => setNewNetwork({ ...newNetwork, ssid: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="OfficeNet"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Security Type</label>
                        <select
                            value={newNetwork.security}
                            onChange={(e) => setNewNetwork({ ...newNetwork, security: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                            <option value="wpa2">WPA2 Personal</option>
                            <option value="wpa3">WPA3 Personal</option>
                            <option value="enterprise">WPA2 Enterprise</option>
                            <option value="open">Open Network</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Band</label>
                        <select
                            value={newNetwork.band}
                            onChange={(e) => setNewNetwork({ ...newNetwork, band: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                            <option value="2.4GHz">2.4GHz</option>
                            <option value="5GHz">5GHz</option>
                            <option value="2.4GHz & 5GHz">Dual Band</option>
                        </select>
                    </div>
                </div>

                {newNetwork.security !== 'open' && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Password</label>
                        <input
                            type="password"
                            required
                            value={newNetwork.password}
                            onChange={(e) => setNewNetwork({ ...newNetwork, password: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="Network password"
                        />
                    </div>
                )}

                <div className="flex justify-end space-x-3 pt-4">
                    <button
                        type="button"
                        onClick={() => document.getElementById('create_network_modal').close()}
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {loading ? 'Creating...' : 'Create Network'}
                    </button>
                </div>
            </form>
        </div>
    </dialog>
);

const CreateUserModal = ({ newUser, setNewUser, handleCreateUser, loading, networks }) => (
    <dialog id="create_user_modal" className="modal">
        <div className="modal-box bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 max-w-2xl">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Add New User</h3>
                <button onClick={() => document.getElementById('create_user_modal').close()} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    <XMarkIcon className="w-6 h-6" />
                </button>
            </div>
            <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email Address</label>
                    <input
                        type="email"
                        required
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="user@example.com"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Role</label>
                    <select
                        value={newUser.role}
                        onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                        <option value="technician">Technician</option>
                        <option value="administrator">Administrator</option>
                        <option value="viewer">Viewer</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Network Access</label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                        {networks.map(network => (
                            <label key={network.id} className="flex items-center space-x-3">
                                <input
                                    type="checkbox"
                                    checked={newUser.networks.includes(network.id)}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setNewUser({ ...newUser, networks: [...newUser.networks, network.id] });
                                        } else {
                                            setNewUser({ ...newUser, networks: newUser.networks.filter(id => id !== network.id) });
                                        }
                                    }}
                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-700 dark:text-gray-300">{network.name}</span>
                            </label>
                        ))}
                    </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                    <button
                        type="button"
                        onClick={() => document.getElementById('create_user_modal').close()}
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {loading ? 'Creating...' : 'Add User'}
                    </button>
                </div>
            </form>
        </div>
    </dialog>
);

const CreateAccessCodeModal = ({ newAccessCode, setNewAccessCode, handleGenerateAccessCode, loading, networks }) => (
    <dialog id="create_code_modal" className="modal">
        <div className="modal-box bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 max-w-2xl">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Generate Access Code</h3>
                <button onClick={() => document.getElementById('create_code_modal').close()} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    <XMarkIcon className="w-6 h-6" />
                </button>
            </div>
            <form onSubmit={handleGenerateAccessCode} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Network</label>
                    <select
                        required
                        value={newAccessCode.network}
                        onChange={(e) => setNewAccessCode({ ...newAccessCode, network: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                        <option value="">Select a network</option>
                        {networks.map(network => (
                            <option key={network.id} value={network.name}>{network.name}</option>
                        ))}
                    </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Maximum Uses</label>
                        <input
                            type="number"
                            required
                            min="1"
                            value={newAccessCode.maxUses}
                            onChange={(e) => setNewAccessCode({ ...newAccessCode, maxUses: parseInt(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Expiration Date</label>
                        <input
                            type="date"
                            required
                            value={newAccessCode.expires}
                            onChange={(e) => setNewAccessCode({ ...newAccessCode, expires: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description (Optional)</label>
                    <input
                        type="text"
                        value={newAccessCode.description}
                        onChange={(e) => setNewAccessCode({ ...newAccessCode, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="e.g., Guest access for conference"
                    />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                    <button
                        type="button"
                        onClick={() => document.getElementById('create_code_modal').close()}
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {loading ? 'Generating...' : 'Generate Code'}
                    </button>
                </div>
            </form>
        </div>
    </dialog>
);

export default AdminPage;
