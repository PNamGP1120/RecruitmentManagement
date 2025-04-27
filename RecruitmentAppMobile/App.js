import React from 'react';
import { StyleSheet, View, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from './components/LoginScreen';
import HomePage from './components/HomePage'; // Giả sử bạn đã tạo MainScreen
// import RegisterScreen from './screens/RegisterScreen'; // Giả sử bạn đã tạo RegisterScreen

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Main" component={HomePage} options={{ headerShown: false }} />
        {/* <Stack.Screen name="Register" component={RegisterScreen} options={{ headerShown: false }} /> */}

      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});