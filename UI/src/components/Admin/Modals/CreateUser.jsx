import { XMarkIcon, EyeIcon, EyeSlashIcon, } from "@heroicons/react/24/outline";

export const CreateUserModal = ({ newUser, setNewUser, handleCreateUser, loading, networks, passwordVisible, setPasswordVisible }) => (
    <dialog id="create_user_modal" className="modal rounded-xl">
        <div className="modal-box bg-white dark:bg-primary-800 border border-gray-200 dark:border-gray-700 w-[400px] max-w-lg rounded-xl p-4">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white select-none">Add New User</h3>
                <button onClick={() => document.getElementById('create_user_modal').close()} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    <XMarkIcon className="w-6 h-6" />
                </button>
            </div>
            <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 select-none">Username</label>
                    <input
                        type="text"
                        required
                        value={newUser.username}
                        onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                        placeholder="luna187"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 select-none">Email Address</label>
                    <input
                        type="email"
                        required
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                        placeholder="user@example.com"
                    />
                </div>

                <div className='relative'>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Password</label>
                    <input
                        type={`${passwordVisible ? 'text' : 'password'}`}
                        required
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                        placeholder="Network password"
                    />
                    <EyeIcon
                        onClick={() => setPasswordVisible(true)}
                        className={`${passwordVisible ? 'hidden' : 'block'} absolute h-4 w-4 right-2 top-10 text-gray-800 dark:stroke-gray-100 cursor-pointer`} />
                    <EyeSlashIcon
                        onClick={() => setPasswordVisible(false)}
                        className={`${passwordVisible ? 'block' : 'hidden'} absolute h-4 w-4 right-2 top-10 text-gray-800 dark:stroke-gray-100 cursor-pointer`} />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 select-none">Role</label>
                    <select
                        value={newUser.role}
                        onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white"
                    >
                        <option value="technician">Technician</option>
                        <option value="administrator">Administrator</option>
                        <option value="viewer">Viewer</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 select-none">Network Access</label>
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
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-primary-700 rounded-lg transition-colors"
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
