import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../core/theme/app_colors.dart';
import '../../l10n/app_localizations.dart';
import '../../services/notification_service.dart';
import '../../main.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  static const _nameKey = 'profile_name';
  static const _surnameKey = 'profile_surname';
  static const _birthdayKey = 'profile_birthday';

  final _nameController = TextEditingController();
  final _surnameController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  bool _isEditing = false;
  String _storedName = '';
  String _storedSurname = '';
  DateTime? _storedBirthday;
  DateTime? _tempBirthday;

  bool _localNotificationsEnabled = true;
  bool _remoteNotificationsEnabled = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;

    setState(() {
      _storedName = prefs.getString(_nameKey) ?? '';
      _storedSurname = prefs.getString(_surnameKey) ?? '';
      _nameController.text = _storedName;
      _surnameController.text = _storedSurname;
      
      final birthdayString = prefs.getString(_birthdayKey);
      _storedBirthday = birthdayString != null ? DateTime.tryParse(birthdayString) : null;
      _tempBirthday = _storedBirthday;
    });
    
    final localEnabled = await NotificationService.instance.isLocalNotificationsEnabled;
    final remoteEnabled = await NotificationService.instance.isRemoteNotificationsEnabled;
    
    if (mounted) {
      setState(() {
        _localNotificationsEnabled = localEnabled;
        _remoteNotificationsEnabled = remoteEnabled;
      });
    }
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;
    
    final prefs = await SharedPreferences.getInstance();
    final newName = _nameController.text.trim();
    final newSurname = _surnameController.text.trim();
    
    await prefs.setString(_nameKey, newName);
    await prefs.setString(_surnameKey, newSurname);
    if (_tempBirthday != null) {
      await prefs.setString(_birthdayKey, _tempBirthday!.toIso8601String());
    } else {
      await prefs.remove(_birthdayKey);
    }

    if (!mounted) return;
    setState(() {
      _storedName = newName;
      _storedSurname = newSurname;
      _storedBirthday = _tempBirthday;
      _isEditing = false;
    });
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(AppLocalizations.of(context)!.profileSaved)),
    );
  }

  void _cancelEdit() {
    setState(() {
      _nameController.text = _storedName;
      _surnameController.text = _storedSurname;
      _tempBirthday = _storedBirthday;
      _isEditing = false;
    });
  }
  
  Future<void> _signInWithGoogle() async {
    try {
      final GoogleSignInAccount googleUser = await GoogleSignIn.instance.authenticate();
      final GoogleSignInAuthentication googleAuth = googleUser.authentication;
      final OAuthCredential credential = GoogleAuthProvider.credential(
        idToken: googleAuth.idToken,
      );

      await FirebaseAuth.instance.signInWithCredential(credential);
      if (mounted) setState(() {});
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context)!.profileGoogleSignInFailed(e.toString()))),
        );
      }
    }
  }

  Future<void> _signOut() async {
    await FirebaseAuth.instance.signOut();
    await GoogleSignIn.instance.signOut();
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _nameController.dispose();
    _surnameController.dispose();
    super.dispose();
  }

  Widget _buildAvatar(User? user) {
    if (user != null && user.photoURL != null) {
      return CircleAvatar(
        radius: 40,
        backgroundImage: NetworkImage(user.photoURL!),
        backgroundColor: AppColors.border,
      );
    }
    return const CircleAvatar(
      radius: 40,
      backgroundColor: AppColors.border,
      child: Icon(Icons.person, size: 40, color: AppColors.muted),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    User? user;
    try {
      if (Firebase.apps.isNotEmpty) {
        user = FirebaseAuth.instance.currentUser;
      }
    } catch (_) {}
    
    final hasName = _storedName.isNotEmpty || _storedSurname.isNotEmpty;
    final displayName = hasName ? '$_storedName $_storedSurname'.trim() : l10n.profileDefaultUser;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(22, 24, 22, 116),
        children: [
          Row(
            children: [
              const Icon(Icons.person_rounded),
              const SizedBox(width: 10),
              Text(
                l10n.profileTitle,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ],
          ),
          const SizedBox(height: 24),
          
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildAvatar(user),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 8),
                          Text(
                            displayName,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                              color: AppColors.ink,
                            ),
                          ),
                          if (user != null && user.email != null) ...[
                            const SizedBox(height: 4),
                            Text(
                              '@${user.email!.split('@').first}',
                              style: const TextStyle(
                                fontSize: 14,
                                color: AppColors.muted,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                          if (_storedBirthday != null) ...[
                            const SizedBox(height: 4),
                            Text(
                              '🎂 ${_storedBirthday!.day.toString().padLeft(2, '0')}/${_storedBirthday!.month.toString().padLeft(2, '0')}/${_storedBirthday!.year}',
                              style: const TextStyle(
                                fontSize: 14,
                                color: AppColors.muted,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    if (!_isEditing)
                      IconButton.filledTonal(
                        onPressed: () {
                          setState(() {
                            _isEditing = true;
                          });
                        },
                        icon: const Icon(Icons.edit_rounded, size: 20),
                        style: IconButton.styleFrom(
                          backgroundColor: AppColors.background,
                          foregroundColor: AppColors.ink,
                        ),
                      ),
                  ],
                ),
                
                if (_isEditing) ...[
                  const SizedBox(height: 24),
                  Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        TextFormField(
                          controller: _nameController,
                          decoration: InputDecoration(
                            labelText: l10n.profileNameLabel,
                            filled: true,
                            fillColor: AppColors.background,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                              borderSide: BorderSide.none,
                            ),
                          ),
                          validator: (val) =>
                              (val == null || val.trim().isEmpty) ? l10n.profileNameRequired : null,
                        ),
                        const SizedBox(height: 14),
                        TextFormField(
                          controller: _surnameController,
                          decoration: InputDecoration(
                            labelText: l10n.profileSurnameLabel,
                            filled: true,
                            fillColor: AppColors.background,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                              borderSide: BorderSide.none,
                            ),
                          ),
                          validator: (val) =>
                              (val == null || val.trim().isEmpty) ? l10n.profileSurnameRequired : null,
                        ),
                        const SizedBox(height: 14),
                        InkWell(
                          onTap: () async {
                            final picked = await showDatePicker(
                              context: context,
                              initialDate: _tempBirthday ?? DateTime.now(),
                              firstDate: DateTime(1900),
                              lastDate: DateTime.now(),
                            );
                            if (picked != null) {
                              setState(() {
                                _tempBirthday = picked;
                              });
                            }
                          },
                          child: InputDecorator(
                            decoration: InputDecoration(
                              labelText: l10n.profileBirthdayLabel,
                              filled: true,
                              fillColor: AppColors.background,
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide.none,
                              ),
                            ),
                            child: Text(
                              _tempBirthday != null 
                                  ? "${_tempBirthday!.day.toString().padLeft(2, '0')}/${_tempBirthday!.month.toString().padLeft(2, '0')}/${_tempBirthday!.year}" 
                                  : l10n.profileBirthdayNotSet,
                              style: TextStyle(
                                color: _tempBirthday != null ? AppColors.ink : AppColors.muted,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton(
                                onPressed: _cancelEdit,
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                ),
                                child: Text(l10n.profileEditCancel),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: FilledButton(
                                onPressed: _saveProfile,
                                style: FilledButton.styleFrom(
                                  backgroundColor: AppColors.ink,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                ),
                                child: Text(l10n.profileEditConfirm),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 12),
          Text(
            l10n.profileSettingsTitle,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(22),
            ),
            child: Column(
              children: [
                SwitchListTile.adaptive(
                  value: _localNotificationsEnabled,
                  onChanged: (val) async {
                    setState(() => _localNotificationsEnabled = val);
                    await NotificationService.instance.setLocalNotificationsEnabled(val);
                  },
                  title: Text(
                    l10n.profileSettingAuthReminders,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  activeTrackColor: AppColors.ink,
                  shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
                  ),
                ),
                const Divider(height: 1, indent: 16, endIndent: 16),
                SwitchListTile.adaptive(
                  value: _remoteNotificationsEnabled,
                  onChanged: (val) async {
                    setState(() => _remoteNotificationsEnabled = val);
                    await NotificationService.instance.setRemoteNotificationsEnabled(val);
                  },
                  title: Text(
                    l10n.profileSettingAiUpdates,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  activeTrackColor: AppColors.ink,
                ),
                const Divider(height: 1, indent: 16, endIndent: 16),
                ListTile(
                  title: Text(
                    l10n.profileSettingLanguage,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.vertical(bottom: Radius.circular(22)),
                  ),
                  trailing: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: Localizations.localeOf(context).languageCode,
                      icon: const Icon(Icons.arrow_drop_down_rounded, color: AppColors.ink),
                      dropdownColor: AppColors.surface,
                      style: const TextStyle(color: AppColors.ink, fontWeight: FontWeight.w600, fontSize: 16),
                      onChanged: (String? newLanguageCode) {
                        if (newLanguageCode != null) {
                          DecoratorAiApp.setLocale(context, Locale(newLanguageCode));
                        }
                      },
                      items: [
                        DropdownMenuItem(
                          value: 'en',
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text('🇺🇸', style: TextStyle(fontSize: 20)),
                              const SizedBox(width: 8),
                              Text(l10n.languageEnglish),
                            ],
                          ),
                        ),
                        DropdownMenuItem(
                          value: 'tr',
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text('🇹🇷', style: TextStyle(fontSize: 20)),
                              const SizedBox(width: 8),
                              Text(l10n.languageTurkish),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          if (user == null)
            FilledButton.icon(
              onPressed: _signInWithGoogle,
              icon: const Icon(Icons.login_rounded),
              label: Text(l10n.profileSignInGoogle),
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.ink,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(22),
                ),
              ),
            )
          else
            OutlinedButton.icon(
              onPressed: _signOut,
              icon: const Icon(Icons.logout_rounded),
              label: Text(l10n.profileSignOut),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.ink,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(22),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
