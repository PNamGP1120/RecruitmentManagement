import React, { useState } from 'react';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, Image, Platform } from 'react-native';

export default function LoginScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const toggleShowPassword = () => {
        setShowPassword(!showPassword);
    };

    const handleLogin = () => {
        // Implement your login logic here
        console.log('Logging in with:', email, password);
    };

    const handleForgotPassword = () => {
        // Implement your forgot password logic here
        console.log('Forgot Password pressed');
    };

    const handleRegister = () => {
        // Implement your register navigation logic here
        console.log('Register pressed');
    };

    const handleContinueWith = (provider) => {
        // Implement your social login logic here
        console.log('Continue with:', provider);
    };

    return (
        <View style={styles.container}>
            {/* Back Arrow */}
            <TouchableOpacity style={styles.backButton}>
                <Text style={styles.backArrow}>&lt;</Text>
            </TouchableOpacity>

            {/* Logo and Title */}
            <Text style={styles.logo}>Jôbizz</Text>
            <Text style={styles.welcome}>Welcome Back 👋</Text>
            <Text style={styles.subtitle}>Let's log in. Apply to jobs!</Text>

            {/* Email Input */}
            <View style={styles.inputContainer}>
                <Image source={require('../assets/LoginScreen/email.png')} style={styles.icon} />
                <TextInput
                    style={styles.input}
                    placeholder="E-mail"
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                />
            </View>

            {/* Password Input */}
            <View style={styles.inputContainer}>
                <Image source={require('../assets/LoginScreen/password.png')} style={styles.icon} />
                <TextInput
                    style={styles.input}
                    placeholder="Password"
                    secureTextEntry={!showPassword}
                    value={password}
                    onChangeText={setPassword}
                />
                <TouchableOpacity onPress={toggleShowPassword} style={styles.eyeIconContainer}>
                    <Image
                        source={showPassword ? require('../assets/LoginScreen/eye.png') : require('../assets/LoginScreen/eye-close.png')}
                        style={styles.eyeIcon}
                    />
                </TouchableOpacity>
            </View>

            {/* Log In Button */}
            <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
                <Text style={styles.loginButtonText}>Log in</Text>
            </TouchableOpacity>

            {/* Forgot Password */}
            <TouchableOpacity style={styles.forgotPasswordButton} onPress={handleForgotPassword}>
                <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
            </TouchableOpacity>

            {/* Or continue with */}
            <View style={styles.dividerContainer}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>Or continue with</Text>
                <View style={styles.dividerLine} />
            </View>

            {/* Social Login Buttons */}
            <View style={styles.socialLoginContainer}>
                <TouchableOpacity style={styles.socialButton} onPress={() => handleContinueWith('apple')}>
                    <Image source={require('../assets/LoginScreen/apple-icon.png')} style={styles.socialIcon} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.socialButton} onPress={() => handleContinueWith('google')}>
                    <Image source={require('../assets/LoginScreen/google-icon.png')} style={styles.socialIcon} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.socialButton} onPress={() => handleContinueWith('facebook')}>
                    <Image source={require('../assets/LoginScreen/facebook-icon.png')} style={styles.socialIcon} />
                </TouchableOpacity>
            </View>

            {/* Register */}
            <View style={styles.registerContainer}>
                <Text style={styles.registerText}>Haven't an account? </Text>
                <TouchableOpacity onPress={handleRegister}>
                    <Text style={styles.registerLink}>Register</Text>
                </TouchableOpacity>
            </View>

            {/* Bottom Navigation Bar (Placeholder) */}
            <View style={styles.bottomNav}>
                {/* Add your bottom navigation icons/buttons here */}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f9f9f9',
        paddingHorizontal: 20,
        paddingTop: Platform.OS === 'ios' ? 50 : 20,
        justifyContent: 'space-between',
    },
    backButton: {
        marginTop: 10,
    },
    backArrow: {
        fontSize: 24,
        color: '#333',
    },
    logo: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#1e56a0',
        marginTop: 20,
    },
    welcome: {
        fontSize: 24,
        color: '#333',
        marginTop: 10,
    },
    subtitle: {
        fontSize: 16,
        color: '#777',
        marginTop: 5,
        marginBottom: 30,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        borderRadius: 8,
        paddingHorizontal: 15,
        marginBottom: 15,
        borderWidth: 1,
        borderColor: '#ddd',
    },
    icon: {
        width: 20,
        height: 20,
        marginRight: 10,
        tintColor: '#777',
    },
    input: {
        flex: 1,
        height: 45,
        fontSize: 16,
        color: '#333',
    },
    eyeIconContainer: {
        padding: 10,
    },
    eyeIcon: {
        width: 20,
        height: 20,
        tintColor: '#777',
    },
    loginButton: {
        backgroundColor: '#1e56a0',
        borderRadius: 8,
        paddingVertical: 15,
        alignItems: 'center',
        marginBottom: 20,
    },
    loginButtonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
    },
    forgotPasswordButton: {
        alignItems: 'center',
        marginBottom: 30,
    },
    forgotPasswordText: {
        color: '#1e56a0',
        fontSize: 16,
    },
    dividerContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 30,
    },
    dividerLine: {
        flex: 1,
        height: 1,
        backgroundColor: '#ddd',
    },
    dividerText: {
        color: '#777',
        marginHorizontal: 10,
        fontSize: 16,
    },
    socialLoginContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 30,
    },
    socialButton: {
        backgroundColor: '#fff',
        borderRadius: 50,
        padding: 12,
        borderWidth: 1,
        borderColor: '#ddd',
    },
    icon: {
        width: 20,
        height: 20,
        marginRight: 10,
        tintColor: '#777',
    },
    input: {
        flex: 1,
        height: 45,
        fontSize: 16,
        color: '#333',
    },
    eyeIconContainer: {
        padding: 10,
    },
    eyeIcon: {
        width: 20,
        height: 20,
        tintColor: '#777',
    },
    loginButton: {
        backgroundColor: '#1e56a0',
        borderRadius: 8,
        paddingVertical: 15,
        alignItems: 'center',
        marginBottom: 20,
    },
    loginButtonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
    },
    forgotPasswordButton: {
        alignItems: 'center',
        marginBottom: 30,
    },
    forgotPasswordText: {
        color: '#1e56a0',
        fontSize: 16,
    },
    dividerContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 30,
    },
    dividerLine: {
        flex: 1,
        height: 1,
        backgroundColor: '#ddd',
    },
    dividerText: {
        color: '#777',
        marginHorizontal: 10,
        fontSize: 16,
    },
    socialLoginContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 30,
    },
    socialButton: {
        backgroundColor: '#fff',
        borderRadius: 50,
        padding: 12,
        borderWidth: 1,
    },
    socialIcon: {
        width: 30,
        height: 30,
    },
    registerContainer: {
        flexDirection: 'row',
        justifyContent: 'center',
        marginBottom: 20,
    },
    registerText: {
        fontSize: 16,
        color: '#777',
    },
    registerLink: {
        fontSize: 16,
        color: '#1e56a0',
        fontWeight: 'bold',
    },
    bottomNav: {
        height: 60,
        backgroundColor: '#fff',
        borderTopWidth: 1,
        borderColor: '#ddd',
        // Add styles for your bottom navigation items
    },
});