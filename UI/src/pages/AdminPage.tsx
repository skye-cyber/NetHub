import {
    getNetworks,
    getDevices,
    getReports,
    getDeviceHistory,
    getUsers,
    getAccessCodes,
    generateAccessCode,
    createUser,
    createNetwork,
    deleteNetwork,
    deleteAccessCode,
    revokeAccessCode,
    get_qr_code,
} from '../services/api';
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
    DocumentChartBarIcon,
    PencilSquareIcon
} from '@heroicons/react/24/outline';
import { CreateUserModal } from '../components/Admin/Modals/CreateUser';
import { CreateNetworkModal } from '../components/Admin/Modals/CreateNetwork';
import { CreateAccessCodeModal } from '../components/Admin/Modals/CreateAccessCode';
import { StateManager } from '../syscore/StatesManager';
import { useState, useEffect } from 'react';

const AdminPage = () => {
    const [activeTab, setActiveTab] = useState('networks');
    const [loading, setLoading] = useState(false);
    const [devices, setDevices] = useState([]);
    const [networks, setNetworks] = useState([{ id: 1, status: "offline", name: 'nethub@1', ssid: "nethub@1", security: 'secure', clients: 2 }]);
    const [users, setUsers] = useState([]);
    const [accessCodes, setAccessCodes] = useState([]);
    const [deviceHistory, setDeviceHistory] = useState([]);
    const [reports, setReports] = useState([]);
    const [passwordVisible, setPasswordVisible] = useState(false);
    const [UserPasswordVisible, SetUserPasswordVisible] = useState(false);

    const [newNetwork, setNewNetwork] = useState({
        name: "",
        ssid: "",
        security: "wpa2",
        band: "2.4GHz",
        password: "",
        vlan: "",
        vinterface: "",
        max_clients: 50
    });

    const [newUser, setNewUser] = useState({
        username: "",
        email: "",
        password: "",
        role: "technician",
        networks: [],
        permissions: []
    });

    const [newAccessCode, setNewAccessCode] = useState({
        code: "",
        network: "",
        max_uses: 10,
        expires_at: "",
        description: ""
    });

    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            await Promise.all([
                loadNetworks(),
                loadUsers(),
                loadAccessCodes(),
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadNetworks = async () => {
        const response = await getNetworks();
        setNetworks(response.data.networks);
    };

    const loadUsers = async () => {
        const response = await getUsers();
        setUsers(response.data.users);
    };

    const loadAccessCodes = async () => {
        const response = await getAccessCodes();
        setAccessCodes(response.data.access_codes);
    };

    const handleCreateNetwork = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await createNetwork(newNetwork);
            setNetworks(prev => [...prev, { ...response.data.network, id: Date.now(), clients: 0, status: 'active' }]);
            setNewNetwork({ name: "", ssid: "", security: "wpa2", band: "2.4GHz", password: "", vlan: "", max_clients: 50, vinterface: "" });
            document.getElementById('create_network_modal').close();
            StateManager.get('showSleakToastFeedback')({ message: "Network created", body: "Network creation" });
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
                await deleteNetwork(networkId);
                setNetworks(prev => prev.filter(network => network.id !== networkId));
                StateManager.get('showSleakToastFeedback')({ message: "Network deleted", body: "Network deletion" });
            } catch (error) {
                console.error('Error deleting network:', error);
            } finally {
                setLoading(false);
            }
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await createUser(newUser);
            setUsers(prev => [...prev, { ...response.data.user, id: Date.now(), status: 'active', lastLogin: 'Never' }]);
            setNewUser({ email: "", role: "technician", networks: [], permissions: [] });
            document.getElementById('create_user_modal').close();
            StateManager.get('showSleakToastFeedback')({ message: "New user created", body: "User creation" });
        } catch (error) {
            console.error('Error creating user:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateAccessCode = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await generateAccessCode(newAccessCode);
            setAccessCodes(prev => [...prev, { ...response.data.access_code, id: Date.now(), uses: 0, status: 'active' }]);
            setNewAccessCode({ network: "", max_uses: 10, expires_at: "", description: "" });
            document.getElementById('create_code_modal').close();
            StateManager.get('showSleakToastFeedback')({ message: "Access code generated", body: "Access code generation" });
        } catch (error) {
            console.error('Error generating access code:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAccessCode = async (codeId) => {
        if (window.confirm('Are you sure you want to delete this code?')) {
            setLoading(true);
            try {
                await deleteAccessCode(codeId);
                setAccessCodes(prev => prev.filter(code => code.id !== codeId));
                StateManager.get('showSleakToastFeedback')({ message: "Access code deleted", body: "Access code deletion" });
            } catch (error) {
                console.error('Error deleting access code:', error);
            } finally {
                setLoading(false);
            }
        }
    };

    const handleRevokeAccessCode = async (codeId) => {
        if (window.confirm('Are you sure you want to revoke this code?')) {
            setLoading(true);
            try {
                await revokeAccessCode(codeId);
                setAccessCodes(prev => prev.filter(code => code.id !== codeId));
                StateManager.get('showSleakToastFeedback')({ message: "Access code revoked", body: "Revoke Access code" });
            } catch (error) {
                console.error('Error revoking access code:', error);
            } finally {
                setLoading(false);
            }
        }
    };

    const handleGenerateQRCode = async (codeId) => {
        if (window.confirm('Generate QR code for this access code?')) {
            setLoading(true);
            try {
                const bandData = {
                    band_id: "band-" + Math.floor(Math.random() * 1000),
                    band_name: "Band Name",
                    band_type: "VIP",
                    additional_info: "Any extra data you want to include"
                };
                const response = await get_qr_code(codeId, bandData);
                if (response && response.qr_code) {
                    displayQRCode(response.qr_code, response.data);
                    StateManager.get('showSleakToastFeedback')({
                        message: "QR code generated",
                        body: "Scan this QR code for access"
                    });
                } else {
                    throw new Error("Failed to generate QR code");
                }
            } catch (error) {
                console.error('Error generating QR code:', error);
                StateManager.get('showSleakToastFeedback')({
                    message: "Error generating QR code",
                    body: error.message || "Please try again"
                });
            } finally {
                setLoading(false);
            }
        }
    };

    const displayQRCode = (qrCodeData, qrData) => {
        console.log('Displaying QR code:', qrCodeData, qrData);
        // Implement modal display as needed
    };

    // Tab Components with Neo-Cyber styling
    const NetworksTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-neo-text flex items-center gap-2">
                    <span className="w-1 h-6 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                    Manage Networks
                </h2>
                <button
                    onClick={() => document.getElementById('create_network_modal').showModal()}
                    className="flex items-center space-x-2 bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium px-4 py-2.5 rounded-xl hover:shadow-neo transition-all duration-300 shadow-md"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>Create Network</span>
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {networks.map(network => (
                    <div key={network.id} className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-6 transition-all duration-300 hover:border-neo-primary/40 dark:hover:border-neo-primary/40 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo">
                        <div className="absolute inset-0 bg-gradient-to-br from-neo-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                                <WifiIcon className="w-7 h-7 text-neo-primary" />
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${network.status === 'active'
                                        ? 'bg-neo-primary/20 text-neo-primary border border-neo-primary/30'
                                        : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30'
                                    }`}>
                                    {network.status}
                                </span>
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-2">{network.name}</h3>
                            <p className="text-gray-500 dark:text-neo-dim text-sm mb-1">SSID: {network.ssid}</p>
                            <p className="text-gray-500 dark:text-neo-dim text-sm mb-1">Security: {network.security.toUpperCase()}</p>
                            <p className="text-gray-500 dark:text-neo-dim text-sm mb-4">
                                <span className="font-semibold text-neo-primary">{network.clients}</span> connected devices
                            </p>
                            <div className="flex space-x-2">
                                <button className="flex-1 bg-gray-100 dark:bg-primary-900/50 text-gray-700 dark:text-neo-dim py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-primary-800/70 transition-colors border border-gray-200 dark:border-neo-primary/20">
                                    Edit
                                </button>
                                <button
                                    onClick={() => handleDeleteNetwork(network.id)}
                                    className="flex-1 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 py-2 rounded-lg text-sm hover:bg-red-100 dark:hover:bg-red-500/20 transition-colors border border-red-200 dark:border-red-500/30"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const UsersTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-neo-text flex items-center gap-2">
                    <span className="w-1 h-6 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                    Manage Users
                </h2>
                <button
                    onClick={() => document.getElementById('create_user_modal').showModal()}
                    className="flex items-center space-x-2 bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium px-4 py-2.5 rounded-xl hover:shadow-neo transition-all duration-300 shadow-md"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>Add User</span>
                </button>
            </div>

            <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 overflow-hidden shadow-md dark:shadow-lg">
                {users.length > 0 ? (
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-primary-950/50 border-b border-gray-200 dark:border-neo-primary/20">
                            <tr>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-neo-dim">User</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-neo-dim">Role</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-neo-dim">Status</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-neo-dim">Last Login</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 dark:text-neo-dim">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-neo-primary/10">
                            {users.map(user => (
                                <tr key={user.id} className="hover:bg-neo-primary/5 dark:hover:bg-neo-primary/5 transition-colors">
                                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-neo-text">{user.username || user.name || user.email}</td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${['admin', 'administrator'].includes(user.role)
                                                ? 'bg-neo-secondary/20 text-neo-secondary border border-neo-secondary/30'
                                                : 'bg-cyber-500/20 text-cyber-600 dark:text-cyber-400 border border-cyber-500/30'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${user.status === 'active'
                                                ? 'bg-neo-primary/20 text-neo-primary border border-neo-primary/30'
                                                : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30'
                                            }`}>
                                            {user.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-neo-dim">{user.lastLogin || 'Never'}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex space-x-3 text-sm">
                                            <button className="flex items-center gap-1 text-neo-primary hover:text-cyber-400 transition-colors">
                                                <PencilSquareIcon className="h-4 w-4" />
                                                <span className="hidden sm:inline">Edit</span>
                                            </button>
                                            <button className="text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 transition-colors">
                                                Remove
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="p-8 text-center text-gray-500 dark:text-neo-dim">No users found</div>
                )}
            </div>
        </div>
    );

    const AccessCodesTab = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-neo-text flex items-center gap-2">
                    <span className="w-1 h-6 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                    Access Codes
                </h2>
                <button
                    onClick={() => document.getElementById('create_code_modal').showModal()}
                    className="flex items-center space-x-2 bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium px-4 py-2.5 rounded-xl hover:shadow-neo transition-all duration-300 shadow-md"
                >
                    <KeyIcon className="w-5 h-5" />
                    <span>Generate Code</span>
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {accessCodes.map((code) => (
                    <div key={code.id} className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-6 transition-all duration-300 hover:border-neo-primary/40 dark:hover:border-neo-primary/40 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo">
                        <div className="absolute inset-0 bg-gradient-to-br from-neo-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                                <KeyIcon className="w-7 h-7 text-neo-accent" />
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${code.status === 'active'
                                        ? 'bg-neo-primary/20 text-neo-primary border border-neo-primary/30'
                                        : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30'
                                    }`}>
                                    {code.status}
                                </span>
                            </div>
                            <h3 className="text-sm sm:text-base font-mono bg-gray-100 dark:bg-primary-900/50 p-2 rounded border border-gray-200 dark:border-neo-primary/20 mb-3 text-gray-900 dark:text-neo-text">
                                {code.code}
                            </h3>
                            <p className="text-gray-500 dark:text-neo-dim text-sm mb-1">Network: {code.network}</p>
                            <p className="text-gray-500 dark:text-neo-dim text-sm mb-1">
                                Uses: <span className="font-semibold text-neo-primary">{code.uses}/{code.max_uses}</span>
                            </p>
                            <p className="text-gray-500 dark:text-neo-dim text-sm mb-4">Expires: {code.expires_at}</p>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => handleGenerateQRCode(code.id)}
                                    className="flex-1 bg-gray-100 dark:bg-primary-900/50 text-gray-700 dark:text-neo-dim py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-primary-800/70 transition-colors border border-gray-200 dark:border-neo-primary/20 flex items-center justify-center"
                                >
                                    <QrCodeIcon className="w-4 h-4 mr-1" />
                                    QR Code
                                </button>
                                <button
                                    onClick={() => handleRevokeAccessCode(code.id)}
                                    className="flex-1 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 py-2 rounded-lg text-sm hover:bg-red-100 dark:hover:bg-red-500/20 transition-colors border border-red-200 dark:border-red-500/30"
                                >
                                    Revoke
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const DeviceHistoryTab = () => (
        <div className="space-y-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-neo-text flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                Device Connection History
            </h2>
            <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-8 shadow-md dark:shadow-lg">
                <p className="text-gray-500 dark:text-neo-dim text-center">
                    Device history analytics and connection logs will be displayed here.
                </p>
            </div>
        </div>
    );

    const ReportsTab = () => (
        <div className="space-y-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-neo-text flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                Network Reports
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-6 transition-all duration-300 hover:border-neo-primary/40 dark:hover:border-neo-primary/40 shadow-md dark:shadow-lg">
                    <DocumentChartBarIcon className="w-10 h-10 text-neo-primary mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-2">Usage Statistics</h3>
                    <p className="text-gray-500 dark:text-neo-dim text-sm">Bandwidth usage and connection trends</p>
                </div>
                <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-6 transition-all duration-300 hover:border-neo-primary/40 dark:hover:border-neo-primary/40 shadow-md dark:shadow-lg">
                    <ShieldCheckIcon className="w-10 h-10 text-neo-primary mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-2">Security Audit</h3>
                    <p className="text-gray-500 dark:text-neo-dim text-sm">Security events and access patterns</p>
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
        <>
            <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark transition-colors duration-300 p-0 sm:p-4">
                {/* Background decorative elements */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                    <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
                </div>

                <div className="relative max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="mb-8 p-2 sm:p-4">
                        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2">
                            <span className="bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent bg-clip-text text-transparent">
                                Network
                            </span>
                            <span className="text-gray-900 dark:text-neo-text"> Administration</span>
                        </h1>
                        <p className="text-gray-500 dark:text-neo-dim text-sm sm:text-base">
                            Manage networks, users, and access controls
                        </p>
                    </div>

                    {/* Main Card with Tabs */}
                    <div className="rounded-2xl bg-white/90 dark:bg-neo-dark/60 backdrop-blur-md border border-gray-200 dark:border-neo-primary/20 shadow-neo-light dark:shadow-neo overflow-hidden">
                        {/* Tab Navigation */}
                        <div className="border-b border-gray-200 dark:border-neo-primary/20">
                            <nav className="flex space-x-1 sm:space-x-8 px-2 sm:px-6 overflow-x-auto">
                                {tabs.map(tab => {
                                    const Icon = tab.icon;
                                    return (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id)}
                                            className={`flex items-center space-x-2 py-4 px-3 border-b-2 font-medium text-sm whitespace-nowrap transition-all duration-300 ${activeTab === tab.id
                                                    ? 'border-neo-primary text-neo-primary'
                                                    : 'border-transparent text-gray-500 dark:text-neo-dim hover:text-gray-700 dark:hover:text-neo-text'
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
                                    <div className="animate-spin rounded-full h-10 w-10 border-2 border-neo-primary border-t-transparent"></div>
                                </div>
                            ) : (
                                ActiveComponent && <ActiveComponent />
                            )}
                        </div>
                    </div>
                </div>

                {/* Modals - These should also be updated with neo-cyber styling */}
                <CreateNetworkModal
                    newNetwork={newNetwork}
                    setNewNetwork={setNewNetwork}
                    handleCreateNetwork={handleCreateNetwork}
                    loading={loading}
                    passwordVisible={passwordVisible}
                    setPasswordVisible={setPasswordVisible}
                />

                <CreateUserModal
                    newUser={newUser}
                    setNewUser={setNewUser}
                    handleCreateUser={handleCreateUser}
                    loading={loading}
                    networks={networks}
                    passwordVisible={UserPasswordVisible}
                    setPasswordVisible={SetUserPasswordVisible}
                />

                <CreateAccessCodeModal
                    newAccessCode={newAccessCode}
                    setNewAccessCode={setNewAccessCode}
                    handleGenerateAccessCode={handleGenerateAccessCode}
                    loading={loading}
                    networks={networks}
                />
            </div>
        </>
    );
};

export default AdminPage;
