import React from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  ScrollView,
} from 'react-native';

const HomePage = () => {
  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTextContainer}>
          <Text style={styles.welcomeText}>Welcome Back!</Text>
          <Text style={styles.nameText}>John Lucas 👋</Text>
        </View>
        <Image
          source={require('../assets/icon.png')} // Thay bằng đường dẫn ảnh profile của bạn
          style={styles.profileImage}
        />
      </View>

      {/* Search Bar */}
      <View style={styles.searchBarContainer}>
        <TextInput
          style={styles.searchBar}
          placeholder="Search a job or position"
          placeholderTextColor="#777"
        />
      </View>

      {/* Featured Jobs */}
      <View style={styles.featuredJobsContainer}>
        <View style={styles.featuredJobsHeader}>
          <Text style={styles.featuredJobsTitle}>Featured Jobs</Text>
          <TouchableOpacity>
            <Text style={styles.seeAllText}>See all</Text>
          </TouchableOpacity>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.jobCard}>
            <Image
              source={require('../assets/icon.png')} // Thay bằng đường dẫn logo công ty
              style={styles.companyLogo}
            />
            <Text style={styles.jobTitle}>Product Designer</Text>
            <Text style={styles.companyName}>Google</Text>
            <View style={styles.jobDetails}>
              <Text style={styles.jobDetailText}>Design</Text>
              <Text style={styles.jobDetailText}>Full-Time</Text>
              <Text style={styles.jobDetailText}>Junior</Text>
            </View>
            <Text style={styles.salaryText}>$160,00/year</Text>
            <Text style={styles.locationText}>California, USA</Text>
          </View>
          {/* Thêm các job card khác vào đây */}
        </ScrollView>
      </View>

      {/* Recommended Jobs */}
      <View style={styles.recommendedJobsContainer}>
        <View style={styles.recommendedJobsHeader}>
          <Text style={styles.recommendedJobsTitle}>Recommended Jobs</Text>
          <TouchableOpacity>
            <Text style={styles.seeAllText}>See all</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.recommendedJobCards}>
          <View style={styles.recommendedJobCard}>
            {/* Nội dung cho Recommended Job 1 */}
            <Text>UX Designer</Text>
            <Text>Dribbble</Text>
            <Text>$80,000/y</Text>
          </View>
          <View style={styles.recommendedJobCard}>
            {/* Nội dung cho Recommended Job 2 */}
            <Text>Sr Engineer</Text>
            <Text>Facebook</Text>
            <Text>$96,000/y</Text>
          </View>
          {/* Thêm các recommended job card khác vào đây */}
        </View>
      </View>

      {/* Bottom Navigation Bar (Placeholder) */}
      <View style={styles.bottomNav}>
        {/* Thêm các icon/button cho bottom navigation vào đây */}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    paddingHorizontal: 20,
    paddingTop: 50,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
    headerTextContainer: {
    flex: 1,
    marginRight: 10,
  },
  welcomeText: {
    fontSize: 16,
    color: '#777',
  },
  nameText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  profileImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  searchBarContainer: {
    marginBottom: 20,
  },
  searchBar: {
    backgroundColor: '#fff',
    borderRadius: 8,
    paddingHorizontal: 15,
    height: 45,
    fontSize: 16,
    color: '#333',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  featuredJobsContainer: {
    marginBottom: 30,
  },
  featuredJobsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  featuredJobsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  seeAllText: {
    color: '#1e56a0',
    fontSize: 16,
  },
  jobCard: {
    backgroundColor: '#e6f0ff',
    borderRadius: 8,
    padding: 15,
    marginRight: 10,
    width: 250, // Điều chỉnh độ rộng của job card
  },
  companyLogo: {
    width: 30,
    height: 30,
    marginBottom: 10,
  },
  jobTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  companyName: {
    fontSize: 16,
    color: '#777',
    marginBottom: 10,
  },
  jobDetails: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  jobDetailText: {
    fontSize: 14,
    color: '#fff',
    backgroundColor: '#1e56a0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 5,
  },
  salaryText: {
    fontSize: 16,
    color: '#333',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  locationText: {
    fontSize: 14,
    color: '#777',
  },
    recommendedJobsContainer: {
    marginBottom: 30,
  },
  recommendedJobsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  recommendedJobsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  recommendedJobCards: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  recommendedJobCard: {
    backgroundColor: '#ffe6f0',
    borderRadius: 8,
    padding: 15,
    width: '48%', // Chia đều không gian cho các card
  },
  bottomNav: {
    height: 60,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderColor: '#ddd',
    // Thêm styles cho bottom navigation items
  },
});

export default HomePage;