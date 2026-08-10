"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ChangePasswordForm } from "@/features/authentication/components/change-password-form";
import { ProfileForm } from "@/features/authentication/components/profile-form";
import { useProfile } from "@/features/authentication/hooks/use-profile";

export default function ProfilePage() {
  const { data: profile, isLoading, isError } = useProfile();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Profile</h1>
        <p className="mt-1 text-body text-text-secondary">Your personal account settings.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Personal information</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="max-w-form space-y-4">
              <Skeleton className="h-11 w-full" />
              <Skeleton className="h-11 w-full" />
              <Skeleton className="h-11 w-full" />
            </div>
          )}
          {isError && (
            <p className="text-body text-danger">Unable to load your profile. Please try again.</p>
          )}
          {profile && <ProfileForm profile={profile} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
        </CardHeader>
        <CardContent>
          <ChangePasswordForm />
        </CardContent>
      </Card>
    </div>
  );
}
