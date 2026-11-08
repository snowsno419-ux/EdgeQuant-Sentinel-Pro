-- EdgeQuant Sentinel hybrid account/group/signal schema for Supabase.
-- Apply in the Supabase SQL Editor using the project owner. The Windows app
-- uses only the public anon/publishable key; never ship a service_role key.
-- Auth is email/password + confirmation.

begin;
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text not null default '',
    role text not null default 'receiver' check (role in ('provider', 'receiver')),
    created_at timestamptz not null default now()
);

create or replace function public.handle_new_edgequant_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    requested_role text;
begin
    requested_role := lower(coalesce(new.raw_user_meta_data ->> 'role', 'receiver'));
    if requested_role not in ('provider', 'receiver') then
        requested_role := 'receiver';
    end if;
    insert into public.profiles(id, display_name, role)
    values (new.id,
            left(coalesce(new.raw_user_meta_data ->> 'display_name', ''), 100),
            requested_role)
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists edgequant_auth_user_profile on auth.users;
create trigger edgequant_auth_user_profile
after insert on auth.users
for each row execute procedure public.handle_new_edgequant_user();

create or replace function public.edgequant_is_provider()
returns boolean
language sql stable security definer
set search_path = public
as $$
    select exists(select 1 from public.profiles p
                  where p.id = auth.uid() and p.role = 'provider');
$$;

create table if not exists public.provider_groups (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    name text not null check (length(name) between 1 and 120),
    description text not null default '',
    visibility text not null default 'private' check (visibility in ('private', 'public')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.provider_group_members (
    id uuid primary key default gen_random_uuid(),
    group_id uuid not null references public.provider_groups(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    member_role text not null default 'receiver' check (member_role in ('owner', 'receiver')),
    joined_at timestamptz not null default now(),
    unique(group_id, user_id)
);

create or replace function public.edgequant_is_group_owner(p_group_id uuid)
returns boolean
language sql stable security definer
set search_path = public
as $$
    select exists(select 1 from public.provider_groups g
                  where g.id = p_group_id and g.owner_id = auth.uid());
$$;

create or replace function public.edgequant_is_group_member(p_group_id uuid)
returns boolean
language sql stable security definer
set search_path = public
as $$
    select exists(select 1 from public.provider_group_members m
                  where m.group_id = p_group_id and m.user_id = auth.uid());
$$;

create or replace function public.edgequant_add_group_owner()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.provider_group_members(group_id, user_id, member_role)
    values (new.id, new.owner_id, 'owner')
    on conflict (group_id, user_id) do nothing;
    return new;
end;
$$;

drop trigger if exists edgequant_group_owner_member on public.provider_groups;
create trigger edgequant_group_owner_member
after insert on public.provider_groups
for each row execute procedure public.edgequant_add_group_owner();

create table if not exists public.provider_group_requests (
    id uuid primary key default gen_random_uuid(),
    group_id uuid not null references public.provider_groups(id) on delete cascade,
    requester_id uuid not null references auth.users(id) on delete cascade,
    status text not null default 'pending' check (status in ('pending', 'approved', 'declined')),
    created_at timestamptz not null default now(),
    reviewed_at timestamptz,
    reviewed_by uuid references auth.users(id) on delete set null
);
create unique index if not exists provider_group_one_pending_request
    on public.provider_group_requests(group_id, requester_id) where status = 'pending';

create table if not exists public.provider_group_invites (
    id uuid primary key default gen_random_uuid(),
    group_id uuid not null references public.provider_groups(id) on delete cascade,
    created_by uuid not null references auth.users(id) on delete cascade,
    token_hash text not null unique,
    expires_at timestamptz not null,
    max_uses integer not null default 100 check (max_uses between 1 and 10000),
    used_count integer not null default 0 check (used_count >= 0),
    revoked_at timestamptz,
    created_at timestamptz not null default now()
);

create table if not exists public.provider_signals (
    id uuid primary key default gen_random_uuid(),
    group_id uuid not null references public.provider_groups(id) on delete cascade,
    provider_id uuid not null references auth.users(id) on delete cascade,
    symbol text not null check (length(symbol) between 1 and 40),
    direction text not null check (direction in ('BUY', 'SELL')),
    entry jsonb not null default 'null'::jsonb,
    stop_loss text not null default '',
    take_profits jsonb not null default '[]'::jsonb,
    status text not null default 'published',
    progress integer not null default 0 check (progress between 0 and 10),
    payload jsonb not null default '{}'::jsonb,
    logo_url text not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.provider_signal_updates (
    id uuid primary key default gen_random_uuid(),
    signal_id uuid not null references public.provider_signals(id) on delete cascade,
    group_id uuid references public.provider_groups(id) on delete cascade,
    provider_id uuid not null references auth.users(id) on delete cascade,
    update_type text not null check (length(update_type) between 1 and 40),
    details jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create or replace function public.edgequant_fill_signal_update_group()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    actual_group_id uuid;
begin
    select s.group_id into actual_group_id
    from public.provider_signals s where s.id = new.signal_id;
    if not found then
        raise exception 'Shared signal not found';
    end if;
    if auth.uid() is null or new.provider_id <> auth.uid() then
        raise exception 'Signal update provider does not match the signed-in account';
    end if;
    -- Never trust a client-supplied group_id; derive it from the signal row.
    new.group_id := actual_group_id;
    return new;
end;
$$;

drop trigger if exists edgequant_signal_update_group on public.provider_signal_updates;
create trigger edgequant_signal_update_group
before insert on public.provider_signal_updates
for each row execute procedure public.edgequant_fill_signal_update_group();

create or replace function public.request_provider_invite(p_token text)
returns jsonb
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    inv public.provider_group_invites%rowtype;
    req_id uuid;
begin
    if auth.uid() is null then
        raise exception 'Sign in with a verified account first';
    end if;
    if not exists(select 1 from public.profiles p
                  where p.id = auth.uid() and p.role = 'receiver') then
        raise exception 'Only Receiver accounts may request access';
    end if;
    select * into inv
    from public.provider_group_invites i
    where i.token_hash = encode(extensions.digest(coalesce(p_token, ''), 'sha256'), 'hex')
      and i.revoked_at is null and i.expires_at > now() and i.used_count < i.max_uses
    for update;
    if not found then
        raise exception 'Invite code is invalid, expired, revoked, or used up';
    end if;
    if public.edgequant_is_group_member(inv.group_id) then
        return jsonb_build_object('group_id', inv.group_id, 'status', 'already_member');
    end if;
    insert into public.provider_group_requests(group_id, requester_id, status)
    values (inv.group_id, auth.uid(), 'pending')
    on conflict (group_id, requester_id) where status = 'pending'
    do update set created_at = now()
    returning id into req_id;
    update public.provider_group_invites
       set used_count = used_count + 1
     where id = inv.id;
    return jsonb_build_object('group_id', inv.group_id, 'request_id', req_id, 'status', 'pending');
end;
$$;

create or replace function public.request_public_provider_group(p_group_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    req_id uuid;
begin
    if auth.uid() is null then
        raise exception 'Sign in with a verified account first';
    end if;
    if not exists(select 1 from public.profiles p
                  where p.id = auth.uid() and p.role = 'receiver') then
        raise exception 'Only Receiver accounts may request group access';
    end if;
    if not exists(select 1 from public.provider_groups g
                  where g.id = p_group_id and g.visibility = 'public') then
        raise exception 'This group is not publicly requestable';
    end if;
    if public.edgequant_is_group_member(p_group_id) then
        return jsonb_build_object('group_id', p_group_id, 'status', 'already_member');
    end if;
    insert into public.provider_group_requests(group_id, requester_id, status)
    values (p_group_id, auth.uid(), 'pending')
    on conflict (group_id, requester_id) where status = 'pending'
    do update set created_at = now()
    returning id into req_id;
    return jsonb_build_object('group_id', p_group_id, 'request_id', req_id, 'status', 'pending');
end;
$$;

create or replace function public.respond_provider_group_request(p_request_id uuid,
                                                                  p_approved boolean)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    req public.provider_group_requests%rowtype;
begin
    select * into req from public.provider_group_requests r
    where r.id = p_request_id for update;
    if not found then
        raise exception 'Join request not found';
    end if;
    if not public.edgequant_is_group_owner(req.group_id) then
        raise exception 'Only the group provider may decide this request';
    end if;
    if req.status <> 'pending' then
        raise exception 'This request has already been reviewed';
    end if;
    if p_approved then
        insert into public.provider_group_members(group_id, user_id, member_role)
        values (req.group_id, req.requester_id, 'receiver')
        on conflict (group_id, user_id) do nothing;
        update public.provider_group_requests
           set status = 'approved', reviewed_at = now(), reviewed_by = auth.uid()
         where id = req.id;
    else
        update public.provider_group_requests
           set status = 'declined', reviewed_at = now(), reviewed_by = auth.uid()
         where id = req.id;
    end if;
    return jsonb_build_object('request_id', req.id,
                              'status', case when p_approved then 'approved' else 'declined' end);
end;
$$;

-- Keep helper/RPC functions unavailable to anonymous callers; no client receives a service-role key.
revoke all on function public.handle_new_edgequant_user() from public, anon, authenticated;
revoke all on function public.edgequant_add_group_owner() from public, anon, authenticated;
revoke all on function public.edgequant_fill_signal_update_group() from public, anon, authenticated;
revoke all on function public.edgequant_touch_updated_at() from public, anon, authenticated;
revoke all on function public.edgequant_is_provider() from public, anon;
revoke all on function public.edgequant_is_group_owner(uuid) from public, anon;
revoke all on function public.edgequant_is_group_member(uuid) from public, anon;
revoke all on function public.request_provider_invite(text) from public, anon;
revoke all on function public.request_public_provider_group(uuid) from public, anon;
revoke all on function public.respond_provider_group_request(uuid, boolean) from public, anon;
grant execute on function public.edgequant_is_provider() to authenticated;
grant execute on function public.edgequant_is_group_owner(uuid) to authenticated;
grant execute on function public.edgequant_is_group_member(uuid) to authenticated;
grant execute on function public.request_provider_invite(text) to authenticated;
grant execute on function public.request_public_provider_group(uuid) to authenticated;
grant execute on function public.respond_provider_group_request(uuid, boolean) to authenticated;

alter table public.profiles enable row level security;
alter table public.provider_groups enable row level security;
alter table public.provider_group_members enable row level security;
alter table public.provider_group_requests enable row level security;
alter table public.provider_group_invites enable row level security;
alter table public.provider_signals enable row level security;
alter table public.provider_signal_updates enable row level security;

drop policy if exists profiles_select_self on public.profiles;
create policy profiles_select_self on public.profiles
for select to authenticated using (id = auth.uid());

-- No client INSERT/UPDATE/DELETE policies on profiles: the auth trigger owns role.
drop policy if exists provider_groups_read_member_or_public on public.provider_groups;
create policy provider_groups_read_member_or_public on public.provider_groups
for select to authenticated
using (visibility = 'public' or public.edgequant_is_group_member(id));
drop policy if exists provider_groups_insert_owner on public.provider_groups;
create policy provider_groups_insert_owner on public.provider_groups
for insert to authenticated
with check (owner_id = auth.uid() and public.edgequant_is_provider());
drop policy if exists provider_groups_update_owner on public.provider_groups;
create policy provider_groups_update_owner on public.provider_groups
for update to authenticated
using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists provider_groups_delete_owner on public.provider_groups;
create policy provider_groups_delete_owner on public.provider_groups
for delete to authenticated using (owner_id = auth.uid());

-- Membership writes are only performed by SECURITY DEFINER trigger/RPC functions.
drop policy if exists group_members_read_self_or_owner on public.provider_group_members;
create policy group_members_read_self_or_owner on public.provider_group_members
for select to authenticated
using (user_id = auth.uid() or public.edgequant_is_group_owner(group_id));

drop policy if exists group_requests_read_requester_or_owner on public.provider_group_requests;
create policy group_requests_read_requester_or_owner on public.provider_group_requests
for select to authenticated
using (requester_id = auth.uid() or public.edgequant_is_group_owner(group_id));
drop policy if exists group_requests_insert_receiver on public.provider_group_requests;
create policy group_requests_insert_receiver on public.provider_group_requests
for insert to authenticated
with check (requester_id = auth.uid()
            and status = 'pending'
            and exists(select 1 from public.profiles p
                       where p.id = auth.uid() and p.role = 'receiver')
            and exists(select 1 from public.provider_groups g
                       where g.id = group_id and g.visibility = 'public')
            and not public.edgequant_is_group_member(group_id));

-- Only the group's owner can create/read/revoke invite hashes.
drop policy if exists group_invites_owner_all on public.provider_group_invites;
create policy group_invites_owner_all on public.provider_group_invites
for all to authenticated
using (created_by = auth.uid() and public.edgequant_is_group_owner(group_id))
with check (created_by = auth.uid() and public.edgequant_is_group_owner(group_id));

-- Members can read signals; only the owning Provider may create/edit/delete.
drop policy if exists provider_signals_read_member on public.provider_signals;
create policy provider_signals_read_member on public.provider_signals
for select to authenticated
using (public.edgequant_is_group_member(group_id));
drop policy if exists provider_signals_insert_owner on public.provider_signals;
create policy provider_signals_insert_owner on public.provider_signals
for insert to authenticated
with check (provider_id = auth.uid() and public.edgequant_is_provider()
            and public.edgequant_is_group_owner(group_id));
drop policy if exists provider_signals_update_owner on public.provider_signals;
create policy provider_signals_update_owner on public.provider_signals
for update to authenticated
using (provider_id = auth.uid() and public.edgequant_is_group_owner(group_id))
with check (provider_id = auth.uid() and public.edgequant_is_group_owner(group_id));
drop policy if exists provider_signals_delete_owner on public.provider_signals;
create policy provider_signals_delete_owner on public.provider_signals
for delete to authenticated
using (provider_id = auth.uid() and public.edgequant_is_group_owner(group_id));

drop policy if exists signal_updates_read_member on public.provider_signal_updates;
create policy signal_updates_read_member on public.provider_signal_updates
for select to authenticated
using (public.edgequant_is_group_member(group_id));
drop policy if exists signal_updates_insert_owner on public.provider_signal_updates;
create policy signal_updates_insert_owner on public.provider_signal_updates
for insert to authenticated
with check (provider_id = auth.uid()
            and public.edgequant_is_group_owner(group_id)
            and exists(select 1 from public.provider_signals s
                       where s.id = signal_id
                         and s.group_id = provider_signal_updates.group_id
                         and s.provider_id = auth.uid()));

create or replace function public.edgequant_touch_updated_at()
returns trigger language plpgsql set search_path = public as $$
begin
    new.updated_at = now();
    return new;
end;
$$;
drop trigger if exists provider_groups_touch_updated_at on public.provider_groups;
create trigger provider_groups_touch_updated_at before update on public.provider_groups
for each row execute procedure public.edgequant_touch_updated_at();
drop trigger if exists provider_signals_touch_updated_at on public.provider_signals;
create trigger provider_signals_touch_updated_at before update on public.provider_signals
for each row execute procedure public.edgequant_touch_updated_at();

-- PostgREST needs table privileges in addition to RLS policies.
grant usage on schema public to authenticated;
grant select on public.profiles to authenticated;
grant select, insert, update, delete on public.provider_groups to authenticated;
grant select on public.provider_group_members to authenticated;
grant select, insert on public.provider_group_requests to authenticated;
grant select, insert, update, delete on public.provider_group_invites to authenticated;
grant select, insert, update, delete on public.provider_signals to authenticated;
grant select, insert on public.provider_signal_updates to authenticated;
revoke all on public.profiles from anon;
revoke all on public.provider_groups, public.provider_group_members,
              public.provider_group_requests, public.provider_group_invites,
              public.provider_signals, public.provider_signal_updates from anon;

commit;
